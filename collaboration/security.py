"""Tenant/workspace isolation, RBAC, audit, and permission validation."""

from collections import defaultdict
from typing import Any

from .models import CollaborationScope


class CollaborationSecurity:
    def __init__(self) -> None:
        self._grants: dict[tuple[str, str, str], set[str]] = defaultdict(set)
        self.audit: list[dict[str, Any]] = []

    def grant(self, scope: CollaborationScope, permissions: set[str]) -> None:
        self._grants[(scope.tenant, scope.workspace, scope.actor)].update(permissions)

    def require(self, scope: CollaborationScope, permission: str) -> None:
        if permission not in self._grants[
            (scope.tenant, scope.workspace, scope.actor)
        ]:
            raise PermissionError(f"{permission} is required.")

    def isolate(self, scope: CollaborationScope, tenant: str, workspace: str) -> None:
        if tenant != scope.tenant:
            raise PermissionError("Cross-tenant collaboration access is denied.")
        if workspace != scope.workspace:
            raise PermissionError("Cross-workspace collaboration access is denied.")

    def record(self, scope: CollaborationScope, action: str, **details: Any) -> None:
        self.audit.append(
            {
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "actor": scope.actor,
                "action": action,
                **details,
            }
        )
