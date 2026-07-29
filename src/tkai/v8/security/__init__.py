"""Compatibility-first security boundaries for V8 metadata coordination."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.contracts import Scope

_SECRET_MARKERS = (
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def filter_secrets(value: object) -> object:
    """Recursively redact likely secrets without mutating the source value."""

    if isinstance(value, Mapping):
        return {
            str(key): (
                "[REDACTED]"
                if any(marker in str(key).lower() for marker in _SECRET_MARKERS)
                else filter_secrets(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return tuple(filter_secrets(item) for item in value)
    return value


@dataclass(frozen=True)
class Principal:
    """RBAC-compatible identity metadata."""

    identifier: str
    roles: frozenset[str] = frozenset({"viewer"})
    tenant: str = "default"
    workspace: str = "default"


class AccessController:
    """Read-only RBAC and isolation checks for registry discovery."""

    ROLE_PERMISSIONS = {
        "viewer": frozenset({"kernel:read"}),
        "operator": frozenset({"kernel:read", "diagnostics:read"}),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self, principal: Principal, permission: str, scope: Scope
    ) -> None:
        permissions = {
            permission_name
            for role in principal.roles
            for permission_name in self.ROLE_PERMISSIONS.get(role, frozenset())
        }
        if "*" not in permissions and permission not in permissions:
            raise PermissionError(permission)
        if principal.tenant != scope.tenant:
            raise PermissionError("tenant isolation")
        if principal.workspace != scope.workspace:
            raise PermissionError("workspace isolation")

    @staticmethod
    def framework_allowed(scope: Scope, framework: str) -> bool:
        return scope.framework in {"*", "kernel", framework}


__all__ = ("AccessController", "Principal", "filter_secrets")
