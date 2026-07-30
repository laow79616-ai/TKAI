"""RBAC, isolation, bounds, secret filtering, and reasoning safety."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.security import filter_secrets
from tkai.v9.reasoning_mesh.contracts import ReasoningScope, validate_safe_metadata


@dataclass(frozen=True)
class Principal:
    identifier: str
    roles: frozenset[str] = frozenset({"reasoning_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    namespaces: frozenset[str] = frozenset({"*"})
    profiles: frozenset[str] = frozenset({"*"})
    contexts: frozenset[str] = frozenset({"*"})


class AccessController:
    PERMISSIONS = {
        "reasoning_viewer": frozenset({"reasoning:read"}),
        "reasoning_auditor": frozenset({"reasoning:read", "reasoning:audit:read"}),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self, principal: Principal, permission: str, scope: ReasoningScope
    ) -> None:
        allowed = {
            permission
            for role in principal.roles
            for permission in self.PERMISSIONS.get(role, frozenset())
        }
        if permission not in allowed and "*" not in allowed:
            raise PermissionError(permission)
        checks = (
            (principal.tenant == scope.tenant, "tenant isolation"),
            (principal.workspace == scope.workspace, "workspace isolation"),
            (
                "*" in principal.namespaces or scope.namespace in principal.namespaces,
                "namespace isolation",
            ),
            (
                "*" in principal.profiles or scope.profile in principal.profiles,
                "profile isolation",
            ),
            (
                "*" in principal.contexts or scope.context in principal.contexts,
                "context isolation",
            ),
        )
        for valid, message in checks:
            if not valid:
                raise PermissionError(message)


def secure_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    safe = validate_safe_metadata(value)
    filtered = filter_secrets(safe)
    if not isinstance(filtered, Mapping):
        raise TypeError("filtered metadata must remain a mapping")
    return filtered


__all__ = ("AccessController", "Principal", "filter_secrets", "secure_metadata")
