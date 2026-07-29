"""RBAC-compatible isolation and secret filtering for coordination reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from tkai.v8.hyper_coordination.contracts import CoordinationScope
from tkai.v8.security import filter_secrets


@dataclass(frozen=True)
class CoordinationPrincipal:
    """Identity metadata for coordination reads."""

    identifier: str
    roles: frozenset[str] = frozenset({"coordination_viewer"})
    tenant: str = "default"
    workspace: str = "default"
    frameworks: frozenset[str] = frozenset({"*"})


class CoordinationAccessController:
    """Enforce RBAC and tenant, workspace, and framework isolation."""

    ROLE_PERMISSIONS = {
        "coordination_viewer": frozenset({"coordination:read"}),
        "coordination_auditor": frozenset(
            {"coordination:read", "coordination:audit:read"}
        ),
        "administrator": frozenset({"*"}),
    }

    def authorize(
        self,
        principal: CoordinationPrincipal,
        permission: str,
        scope: CoordinationScope,
    ) -> None:
        permissions = {
            item
            for role in principal.roles
            for item in self.ROLE_PERMISSIONS.get(role, frozenset())
        }
        if permission not in permissions and "*" not in permissions:
            raise PermissionError(permission)
        if principal.tenant != scope.tenant:
            raise PermissionError("tenant isolation")
        if principal.workspace != scope.workspace:
            raise PermissionError("workspace isolation")
        if (
            "*" not in principal.frameworks
            and scope.framework not in principal.frameworks
        ):
            raise PermissionError("framework isolation")


def secure_metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return secret-filtered metadata."""

    filtered = filter_secrets(value)
    if not isinstance(filtered, Mapping):
        raise TypeError("filtered coordination metadata must remain a mapping")
    return filtered


__all__ = (
    "CoordinationAccessController",
    "CoordinationPrincipal",
    "filter_secrets",
    "secure_metadata",
)
