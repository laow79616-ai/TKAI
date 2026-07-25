"""Immutable Enterprise architecture models without persistence or authentication."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType


def _metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a read-only metadata snapshot for architecture-only models."""
    return MappingProxyType(dict(value))


class LicenseEdition(str, Enum):
    """Documented commercial editions; enforcement is intentionally absent."""

    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class DeploymentMode(str, Enum):
    """Target deployment topologies; no deployment implementation is supplied."""

    SINGLE_NODE = "single_node"
    CLUSTER = "cluster"
    HIGH_AVAILABILITY = "high_availability"
    KUBERNETES = "kubernetes"


class IdentityProtocol(str, Enum):
    """Identity federation protocols reserved for a future explicit adapter."""

    OIDC = "oidc"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LDAP = "ldap"
    JWT = "jwt"


class AuditOperation(str, Enum):
    """Audit operation categories, independent of any storage or transport."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    EXECUTE = "execute"
    LOGIN = "login"


@dataclass(frozen=True, slots=True)
class Permission:
    """A resource/action permission descriptor with optional safe metadata."""

    permission_id: str
    resource: str
    action: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.permission_id or not self.resource or not self.action:
            raise ValueError("Permission fields must not be empty.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Role:
    """A named RBAC role referencing declared permission identifiers."""

    role_id: str
    name: str
    permission_ids: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.role_id or not self.name:
            raise ValueError("Role id and name must not be empty.")
        object.__setattr__(self, "permission_ids", frozenset(self.permission_ids))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class User:
    """A user identity reference, not a credential, session, or login record."""

    user_id: str
    display_name: str
    role_ids: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.user_id or not self.display_name:
            raise ValueError("User id and display name must not be empty.")
        object.__setattr__(self, "role_ids", frozenset(self.role_ids))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Team:
    """A team within a workspace, represented only by immutable member references."""

    team_id: str
    workspace_id: str
    name: str
    member_ids: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True, slots=True)
class Workspace:
    """A workspace ownership boundary inside a department and organization."""

    workspace_id: str
    department_id: str
    name: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Department:
    """A department reference owned by one organization."""

    department_id: str
    organization_id: str
    name: str


@dataclass(frozen=True, slots=True)
class Organization:
    """An organization/company root with no implicit tenant provisioning."""

    organization_id: str
    name: str
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.organization_id or not self.name:
            raise ValueError("Organization id and name must not be empty.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class Quota:
    """A declared tenant quota; no limiter or enforcement behavior is implemented."""

    name: str
    limit: int | None
    unit: str

    def __post_init__(self) -> None:
        if not self.name or not self.unit or self.limit is not None and self.limit < 0:
            raise ValueError("Quota name/unit and non-negative limit are required.")


@dataclass(frozen=True, slots=True)
class Tenant:
    """A tenant isolation descriptor with explicit quotas and metadata only."""

    tenant_id: str
    organization_id: str
    name: str
    quotas: tuple[Quota, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id or not self.organization_id or not self.name:
            raise ValueError("Tenant fields must not be empty.")
        object.__setattr__(self, "quotas", tuple(self.quotas))
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class LicenseDescriptor:
    """A license edition declaration; entitlement validation is not implemented."""

    edition: LicenseEdition
    organization_id: str | None = None
    features: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", frozenset(self.features))


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """An immutable audit event for future compliance storage adapters."""

    event_id: str
    tenant_id: str
    actor_id: str | None
    operation: AuditOperation
    resource: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_id or not self.tenant_id or not self.resource:
            raise ValueError("Audit event identifiers and resource must not be empty.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))


@dataclass(frozen=True, slots=True)
class DeploymentProfile:
    """A declarative deployment target without Kubernetes or cluster automation."""

    mode: DeploymentMode
    replicas: int = 1
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.replicas < 1:
            raise ValueError("Deployment replicas must be at least one.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))
