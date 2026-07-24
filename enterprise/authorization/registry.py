"""Thread-safe reference registries for injected RBAC descriptors only."""

from __future__ import annotations

from threading import RLock

from .errors import AuthorizationConflictError, AuthorizationNotFoundError
from .models import PermissionDescriptor, RoleDescriptor


class ReferenceRoleRegistry:
    """Explicit in-memory registry with stable snapshots and no persistence."""

    def __init__(self) -> None:
        self._roles: dict[str, RoleDescriptor] = {}
        self._lock = RLock()

    def register(self, role: RoleDescriptor) -> None:
        """Register a caller-provided role descriptor."""
        with self._lock:
            if role.role_id in self._roles:
                raise AuthorizationConflictError(f"Role {role.role_id!r} is duplicate.")
            self._roles[role.role_id] = role

    def get(self, role_id: str) -> RoleDescriptor:
        """Look up one descriptor without mutation."""
        with self._lock:
            try:
                return self._roles[role_id]
            except KeyError as exc:
                raise AuthorizationNotFoundError(
                    f"Role {role_id!r} was not found."
                ) from exc

    def list(self) -> tuple[RoleDescriptor, ...]:
        """Return a deterministic immutable role snapshot."""
        with self._lock:
            return tuple(self._roles[key] for key in sorted(self._roles))


class ReferencePermissionRegistry:
    """Explicit in-memory permission registry with no policy installation behavior."""

    def __init__(self) -> None:
        self._permissions: dict[str, PermissionDescriptor] = {}
        self._lock = RLock()

    def register(self, permission: PermissionDescriptor) -> None:
        """Register a caller-provided permission descriptor."""
        with self._lock:
            if permission.permission_id in self._permissions:
                raise AuthorizationConflictError(
                    f"Permission {permission.permission_id!r} is duplicate."
                )
            self._permissions[permission.permission_id] = permission

    def get(self, permission_id: str) -> PermissionDescriptor:
        """Look up one immutable permission descriptor."""
        with self._lock:
            try:
                return self._permissions[permission_id]
            except KeyError as exc:
                raise AuthorizationNotFoundError(
                    f"Permission {permission_id!r} was not found."
                ) from exc

    def list(self) -> tuple[PermissionDescriptor, ...]:
        """Return a deterministic immutable permission snapshot."""
        with self._lock:
            return tuple(self._permissions[key] for key in sorted(self._permissions))
