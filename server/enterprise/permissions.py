"""Explicit deny-by-default RBAC evaluation."""

from __future__ import annotations

from .errors import EnterprisePermissionError
from .models import (
    ALL_PERMISSIONS,
    Permission,
    RoleAssignment,
    RoleId,
    RoleRecord,
    UserId,
)


def builtin_roles() -> tuple[RoleRecord, ...]:
    """Return stable built-in role descriptions without shared mutable state."""
    return (
        RoleRecord(
            RoleId("super_admin"), "super_admin", tuple(sorted(ALL_PERMISSIONS))
        ),
        RoleRecord(
            RoleId("organization_admin"),
            "organization_admin",
            (
                "organizations.read",
                "organizations.write",
                "teams.read",
                "teams.write",
                "users.read",
                "roles.read",
            ),
        ),
        RoleRecord(
            RoleId("publisher_manager"),
            "publisher_manager",
            ("publisher.read", "publisher.write"),
        ),
        RoleRecord(
            RoleId("package_manager"),
            "package_manager",
            ("package.read", "package.write", "version.read", "version.write"),
        ),
        RoleRecord(
            RoleId("viewer"),
            "viewer",
            (
                "audit.read",
                "health.read",
                "package.read",
                "publisher.read",
                "registry.read",
                "search.read",
                "statistics.read",
                "version.read",
            ),
        ),
    )


class AuthorizationService:
    """Evaluate roles supplied by explicit storage; deny permission by default."""

    def allowed(
        self,
        user_id: UserId,
        permission: Permission,
        roles: tuple[RoleRecord, ...],
        assignments: tuple[RoleAssignment, ...],
    ) -> bool:
        assigned = {
            str(item.role_id) for item in assignments if item.user_id == user_id
        }
        return any(
            str(role.role_id) in assigned and permission in role.permissions
            for role in roles
        )

    def require(
        self,
        user_id: UserId,
        permission: Permission,
        roles: tuple[RoleRecord, ...],
        assignments: tuple[RoleAssignment, ...],
    ) -> None:
        if not self.allowed(user_id, permission, roles, assignments):
            raise EnterprisePermissionError("Permission denied.")


class PermissionEvaluator:
    """The sole bridge from authenticated identity to explicit RBAC evaluation."""

    def __init__(self, authorization: AuthorizationService | None = None) -> None:
        self._authorization = authorization or AuthorizationService()

    def require(
        self,
        user_id: UserId,
        permission: Permission,
        roles: tuple[RoleRecord, ...],
        assignments: tuple[RoleAssignment, ...],
        *,
        legacy_administrator: bool = False,
    ) -> None:
        """Allow legacy admin explicitly; otherwise apply deny-by-default RBAC."""
        if legacy_administrator:
            return
        self._authorization.require(user_id, permission, roles, assignments)
