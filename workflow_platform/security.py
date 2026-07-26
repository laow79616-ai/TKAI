"""Workflow authorization, isolation, secret, limit, and audit controls."""

from dataclasses import dataclass, field
from typing import Any

from .models import Scope


@dataclass(slots=True)
class SecurityPolicy:
    permissions: dict[tuple[str, str], frozenset[str]] = field(default_factory=dict)
    audit_events: list[dict[str, Any]] = field(default_factory=list)

    def grant(self, actor: str, scope: Scope, permissions: set[str]) -> None:
        self.permissions[(actor, f"{scope.tenant}/{scope.workspace}")] = frozenset(
            permissions
        )
        self.audit("permission.granted", actor, scope, {"permissions": permissions})

    def require(self, actor: str, scope: Scope, permission: str) -> None:
        allowed = self.permissions.get(
            (actor, f"{scope.tenant}/{scope.workspace}"), frozenset()
        )
        if permission not in allowed:
            raise PermissionError("Workflow permission denied.")
        self.audit("permission.validated", actor, scope, {"permission": permission})

    def audit(
        self, event: str, actor: str, scope: Scope, details: dict[str, Any]
    ) -> None:
        safe = {
            key: "[REDACTED]"
            if key.lower() in {"secret", "password", "token", "authorization"}
            else value
            for key, value in details.items()
        }
        self.audit_events.append(
            {"event": event, "actor": actor, "scope": scope, "details": safe}
        )
