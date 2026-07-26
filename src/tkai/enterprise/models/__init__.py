"""Immutable models for the TKAI enterprise product layer."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class Edition(str, Enum):
    COMMUNITY = "community"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class AuditAction(str, Enum):
    LOGIN = "user.login"
    LOGOUT = "user.logout"
    ROLE_CHANGE = "role.change"
    PERMISSION_CHANGE = "permission.change"
    TENANT_CHANGE = "tenant.change"
    PLUGIN_INSTALL = "plugin.install"
    AGENT_RUN = "agent.run"
    WORKFLOW_RUN = "workflow.run"
    API_ACCESS = "api.access"


@dataclass(frozen=True, slots=True)
class Quota:
    seats: int = 1
    monthly_runs: int = 1_000
    storage_bytes: int = 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        if min(self.seats, self.monthly_runs, self.storage_bytes) < 0:
            raise ValueError("quota values must not be negative")


@dataclass(frozen=True, slots=True)
class Organization:
    organization_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Tenant:
    tenant_id: str
    organization_id: str
    name: str
    namespace: str
    quota: Quota = Quota()


@dataclass(frozen=True, slots=True)
class Workspace:
    workspace_id: str
    tenant_id: str
    namespace: str


@dataclass(frozen=True, slots=True)
class User:
    user_id: str
    tenant_id: str
    email: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class Permission:
    permission_id: str
    action: str
    resource: str


@dataclass(frozen=True, slots=True)
class Role:
    role_id: str
    name: str
    permissions: frozenset[str] = frozenset()
    parent_role_id: str | None = None
    scope: str = "*"


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    user_id: str
    role_id: str
    tenant_id: str
    scope: str = "*"


@dataclass(frozen=True, slots=True)
class IdentityProvider:
    provider_id: str
    protocol: str
    issuer: str
    client_id: str = ""
    directory: str = ""


@dataclass(frozen=True, slots=True)
class License:
    key: str
    tenant_id: str
    edition: Edition
    seats: int
    activated_at: float
    expires_at: float


@dataclass(frozen=True, slots=True)
class Plan:
    plan_id: str
    name: str
    quota: Quota
    price_minor: int = 0


@dataclass(frozen=True, slots=True)
class Subscription:
    subscription_id: str
    tenant_id: str
    plan_id: str
    active: bool = True


@dataclass(frozen=True, slots=True)
class Usage:
    tenant_id: str
    metric: str
    quantity: int


@dataclass(frozen=True, slots=True)
class AuditEvent:
    sequence: int
    action: AuditAction
    actor_id: str
    tenant_id: str
    resource: str
    timestamp: float
    metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


__all__ = (
    "AuditAction",
    "AuditEvent",
    "Edition",
    "IdentityProvider",
    "License",
    "Organization",
    "Permission",
    "Plan",
    "Quota",
    "Role",
    "RoleAssignment",
    "Subscription",
    "Tenant",
    "Usage",
    "User",
    "Workspace",
)
