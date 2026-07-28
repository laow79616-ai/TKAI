"""RBAC, tenant isolation, execution limits, secrets, and audit."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from .models import Scope


class OrchestratorSecurity:
    def __init__(self, execution_limit: int = 100) -> None:
        self.execution_limit = execution_limit
        self._grants: dict[tuple[str, str], set[str]] = defaultdict(set)
        self.audit: list[dict[str, Any]] = []

    def grant(self, scope: Scope, permissions: set[str]) -> None:
        self._grants[(scope.tenant, scope.actor)].update(permissions)

    def require(self, scope: Scope, permission: str) -> None:
        if permission not in self._grants[(scope.tenant, scope.actor)]:
            raise PermissionError(f"{permission} is required.")
        self.record(scope, permission)

    def isolate(self, expected: Scope, actual: Scope) -> None:
        if expected.tenant != actual.tenant:
            raise PermissionError("Cross-tenant access is denied.")

    def validate_secrets(self, value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if "secret" in key.lower() and not (
                    isinstance(item, str) and item.startswith("secret://")
                ):
                    raise ValueError("Secrets must use secret:// references.")
                self.validate_secrets(item)
        elif isinstance(value, list):
            for item in value:
                self.validate_secrets(item)

    def record(self, scope: Scope, action: str, **details: Any) -> None:
        self.audit.append(
            {"tenant": scope.tenant, "actor": scope.actor, "action": action, **details}
        )
