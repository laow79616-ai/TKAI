"""Security boundaries for governance operations and reporting."""

from __future__ import annotations

from typing import Any

from .entities import GovernanceScope

SENSITIVE_KEYS = {"secret", "token", "password", "api_key", "credential"}


class GovernanceSecurity:
    def __init__(self, max_export_records: int = 1000) -> None:
        self.permissions: dict[tuple[str, str, str], set[str]] = {}
        self.max_export_records = max_export_records

    def grant(self, scope: GovernanceScope, permissions: set[str]) -> None:
        self.permissions.setdefault(
            (scope.tenant, scope.workspace, scope.actor), set()
        ).update(permissions)

    def require(self, scope: GovernanceScope, permission: str) -> None:
        allowed = self.permissions.get(
            (scope.tenant, scope.workspace, scope.actor), set()
        )
        if permission not in allowed and "governance:admin" not in allowed:
            raise PermissionError(f"Missing governance permission: {permission}.")

    def validate_resource(
        self, tenant: str, workspace: str, scope: GovernanceScope
    ) -> None:
        if tenant != scope.tenant:
            raise PermissionError("Cross-tenant governance access is denied.")
        if workspace != scope.workspace:
            raise PermissionError("Cross-workspace governance access is denied.")

    def redact(self, value: Any) -> Any:
        if isinstance(value, dict):
            return {
                str(key): (
                    "[REDACTED]"
                    if str(key).lower() in SENSITIVE_KEYS
                    else self.redact(item)
                )
                for key, item in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self.redact(item) for item in value]
        return value

    def bound_export(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(records) > self.max_export_records:
            raise ValueError("Governance export exceeds the bounded export size.")
        return [self.redact(record) for record in records]
