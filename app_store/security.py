"""Scoped permissions and bounded package security controls."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field

from .models import Package, Scope

PERMISSIONS = frozenset(
    {
        "install",
        "update",
        "uninstall",
        "publish",
        "review",
        "moderate",
        "manage_licenses",
        "manage_subscriptions",
    }
)


@dataclass(slots=True)
class SecurityPolicy:
    maximum_package_bytes: int = 512 * 1024 * 1024
    maximum_dependency_depth: int = 16
    grants: dict[tuple[str, Scope], frozenset[str]] = field(default_factory=dict)
    audit: list[dict[str, object]] = field(default_factory=list)

    def grant(self, actor: str, scope: Scope, permissions: set[str]) -> None:
        unknown = permissions - PERMISSIONS
        if unknown:
            raise ValueError(f"Unknown permissions: {sorted(unknown)}")
        self.grants[(actor, scope)] = frozenset(permissions)

    def require(self, actor: str, scope: Scope, permission: str) -> None:
        if permission not in self.grants.get((actor, scope), frozenset()):
            raise PermissionError("App Store permission denied for this scope.")

    def validate_package(self, package: Package, signing_identity: str) -> None:
        if package.size_bytes < 0 or package.size_bytes > self.maximum_package_bytes:
            raise ValueError("Package size exceeds the configured bound.")
        if len(package.dependencies) > self.maximum_dependency_depth:
            raise ValueError("Dependency depth exceeds the configured bound.")
        if package.manifest.get("shell") or package.manifest.get("command"):
            raise ValueError("Arbitrary shell execution is prohibited.")
        if package.manifest.get("unrestricted_network"):
            raise ValueError("Unrestricted network access is prohibited.")
        expected = hashlib.sha256(package.artifact_reference.encode()).hexdigest()
        if not hmac.compare_digest(expected, package.checksum):
            raise ValueError("Package checksum validation failed.")
        signature = hashlib.sha256(
            f"{signing_identity}:{package.checksum}".encode()
        ).hexdigest()
        if not hmac.compare_digest(signature, package.signature):
            raise ValueError("Package signature validation failed.")

    def record(
        self, event: str, actor: str, scope: Scope, details: dict[str, object]
    ) -> None:
        secret_names = {"secret", "password", "token", "authorization", "license_key"}
        safe = {
            key: "[REDACTED]" if key.lower() in secret_names else value
            for key, value in details.items()
        }
        self.audit.append(
            {"event": event, "actor": actor, "scope": scope, "details": safe}
        )
