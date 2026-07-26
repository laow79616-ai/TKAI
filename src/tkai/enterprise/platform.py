"""Thread-safe, dependency-free Enterprise Platform reference service."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import fields, is_dataclass
from enum import Enum
from threading import RLock
from time import time
from typing import Any, TypeVar, cast

from .models import (
    AuditAction,
    AuditEvent,
    IdentityProvider,
    License,
    Organization,
    Permission,
    Plan,
    Role,
    RoleAssignment,
    Subscription,
    Tenant,
    Usage,
    User,
    Workspace,
)

T = TypeVar("T")


class EnterprisePlatform:
    """Own tenant-scoped records while leaving persistence and IdP I/O to adapters."""

    def __init__(self, clock: Callable[[], float] = time) -> None:
        self._clock = clock
        self._lock = RLock()
        self._organizations: dict[str, Organization] = {}
        self._tenants: dict[str, Tenant] = {}
        self._workspaces: dict[str, Workspace] = {}
        self._users: dict[str, User] = {}
        self._permissions: dict[str, Permission] = {}
        self._roles: dict[str, Role] = {}
        self._assignments: list[RoleAssignment] = []
        self._providers: dict[str, IdentityProvider] = {}
        self._licenses: dict[str, License] = {}
        self._plans: dict[str, Plan] = {}
        self._subscriptions: dict[str, Subscription] = {}
        self._usage: list[Usage] = []
        self._audit: list[AuditEvent] = []

    def add_organization(self, value: Organization) -> Organization:
        return self._put(self._organizations, value.organization_id, value)

    def add_tenant(self, value: Tenant) -> Tenant:
        with self._lock:
            if value.organization_id not in self._organizations:
                raise ValueError("tenant organization does not exist")
            return self._put(self._tenants, value.tenant_id, value)

    def add_workspace(self, value: Workspace) -> Workspace:
        self._require_tenant(value.tenant_id)
        return self._put(self._workspaces, value.workspace_id, value)

    def add_user(self, value: User) -> User:
        self._require_tenant(value.tenant_id)
        self._enforce_seats(value.tenant_id)
        return self._put(self._users, value.user_id, value)

    def add_permission(self, value: Permission) -> Permission:
        return self._put(self._permissions, value.permission_id, value)

    def add_role(self, value: Role) -> Role:
        if value.parent_role_id and value.parent_role_id not in self._roles:
            raise ValueError("parent role does not exist")
        unknown = value.permissions - self._permissions.keys()
        if unknown:
            raise ValueError(f"unknown permissions: {sorted(unknown)}")
        return self._put(self._roles, value.role_id, value)

    def assign_role(self, value: RoleAssignment) -> RoleAssignment:
        self._require_tenant(value.tenant_id)
        user = self._users.get(value.user_id)
        if user is None or user.tenant_id != value.tenant_id:
            raise ValueError("role assignment crosses tenant boundary")
        if value.role_id not in self._roles:
            raise ValueError("role does not exist")
        with self._lock:
            if value not in self._assignments:
                self._assignments.append(value)
            return value

    def permits(self, user_id: str, tenant_id: str, action: str, resource: str) -> bool:
        role_ids = {
            item.role_id
            for item in self._assignments
            if item.user_id == user_id
            and item.tenant_id == tenant_id
            and (item.scope == "*" or resource.startswith(item.scope))
        }
        visited: set[str] = set()
        while role_ids:
            role_id = role_ids.pop()
            if role_id in visited:
                continue
            visited.add(role_id)
            role = self._roles[role_id]
            for permission_id in role.permissions:
                permission = self._permissions[permission_id]
                resource_matches = permission.resource in (
                    resource,
                    "*",
                ) or resource.endswith(f"/{permission.resource}")
                if permission.action in (action, "*") and resource_matches:
                    return True
            if role.parent_role_id:
                role_ids.add(role.parent_role_id)
        return False

    def add_identity_provider(self, value: IdentityProvider) -> IdentityProvider:
        if value.protocol not in {"oidc", "oauth2", "ldap", "active_directory"}:
            raise ValueError("unsupported identity provider protocol")
        return self._put(self._providers, value.provider_id, value)

    def activate_license(self, value: License) -> License:
        self._require_tenant(value.tenant_id)
        if value.seats <= 0 or value.expires_at <= value.activated_at:
            raise ValueError("invalid license")
        return self._put(self._licenses, value.tenant_id, value, replace=True)

    def validate_license(self, tenant_id: str, at: float | None = None) -> bool:
        license_ = self._licenses.get(tenant_id)
        instant = self._clock() if at is None else at
        return bool(license_ and license_.activated_at <= instant < license_.expires_at)

    def add_plan(self, value: Plan) -> Plan:
        return self._put(self._plans, value.plan_id, value)

    def subscribe(self, value: Subscription) -> Subscription:
        self._require_tenant(value.tenant_id)
        if value.plan_id not in self._plans:
            raise ValueError("billing plan does not exist")
        return self._put(self._subscriptions, value.tenant_id, value, replace=True)

    def record_usage(self, value: Usage) -> Usage:
        self._require_tenant(value.tenant_id)
        if value.quantity < 0:
            raise ValueError("usage must not be negative")
        with self._lock:
            self._usage.append(value)
        return value

    def record_audit(
        self,
        action: AuditAction,
        actor_id: str,
        tenant_id: str,
        resource: str,
        metadata: dict[str, str] | None = None,
    ) -> AuditEvent:
        self._require_tenant(tenant_id)
        with self._lock:
            event = AuditEvent(
                len(self._audit) + 1,
                action,
                actor_id,
                tenant_id,
                resource,
                self._clock(),
                metadata or {},
            )
            self._audit.append(event)
            return event

    def list_records(
        self, kind: str, tenant_id: str | None = None
    ) -> tuple[object, ...]:
        sources: dict[str, object] = {
            "organizations": self._organizations,
            "tenants": self._tenants,
            "users": self._users,
            "roles": self._roles,
            "permissions": self._permissions,
            "license": self._licenses,
            "billing": self._subscriptions,
        }
        if kind == "audit":
            values: tuple[object, ...] = tuple(self._audit)
        else:
            source = sources.get(kind)
            if not isinstance(source, dict):
                raise ValueError(f"unknown enterprise resource: {kind}")
            values = tuple(source[key] for key in sorted(source))
        if tenant_id is None:
            return values
        return tuple(
            value for value in values if getattr(value, "tenant_id", None) == tenant_id
        )

    def metrics(self) -> dict[str, int]:
        return {
            "tenant_total": len(self._tenants),
            "organization_total": len(self._organizations),
            "user_total": len(self._users),
            "license_total": len(self._licenses),
            "audit_total": len(self._audit),
        }

    @staticmethod
    def serialize(value: object) -> dict[str, object]:
        if not is_dataclass(value) or isinstance(value, type):
            raise TypeError("enterprise records must be dataclass instances")
        result = {
            item.name: EnterprisePlatform._json_value(getattr(value, item.name))
            for item in fields(value)
        }
        return cast(dict[str, object], result)

    @staticmethod
    def _json_value(value: Any) -> object:
        if isinstance(value, Enum):
            return value.value
        if isinstance(value, Mapping):
            return {
                str(key): EnterprisePlatform._json_value(item)
                for key, item in value.items()
            }
        if is_dataclass(value) and not isinstance(value, type):
            return EnterprisePlatform.serialize(value)
        if isinstance(value, (set, frozenset, tuple, list)):
            return [EnterprisePlatform._json_value(item) for item in value]
        return value

    def _require_tenant(self, tenant_id: str) -> None:
        if tenant_id not in self._tenants:
            raise ValueError("tenant does not exist")

    def _enforce_seats(self, tenant_id: str) -> None:
        license_ = self._licenses.get(tenant_id)
        seat_limit = (
            license_.seats if license_ else self._tenants[tenant_id].quota.seats
        )
        used = sum(
            user.tenant_id == tenant_id and user.active for user in self._users.values()
        )
        if used >= seat_limit:
            raise ValueError("tenant seat quota exceeded")

    def _put(
        self, target: dict[str, T], key: str, value: T, replace: bool = False
    ) -> T:
        with self._lock:
            if not replace and key in target:
                raise ValueError(f"duplicate enterprise id: {key}")
            target[key] = value
            return value
