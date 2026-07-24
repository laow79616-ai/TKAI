"""Immutable tenant, organization binding, and membership boundary descriptors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType

TenantValue = str | int | float | bool | None


def snapshot(value: Mapping[str, TenantValue]) -> Mapping[str, TenantValue]:
    """Return a defensive metadata snapshot without credentials or connections."""
    return MappingProxyType(dict(value))


class TenantStatus(str, Enum):
    """Declarative lifecycle statuses; no resource operation is implied."""

    PROVISIONED = "provisioned"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class Tenant:
    """Full immutable tenant descriptor with no persistent backing store."""

    tenant_id: str
    name: str
    slug: str
    organization_id: str
    status: TenantStatus = TenantStatus.ACTIVE
    edition: str | None = None
    region: str | None = None
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if (
            not self.tenant_id
            or not self.name
            or not self.slug
            or not self.organization_id
        ):
            raise ValueError("Tenant id, name, slug, and organization id are required.")
        if self.created_at.tzinfo is None or self.updated_at.tzinfo is None:
            raise ValueError("Tenant timestamps must be timezone-aware.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))
        object.__setattr__(self, "created_at", self.created_at.astimezone(timezone.utc))
        object.__setattr__(self, "updated_at", self.updated_at.astimezone(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe tenant snapshot."""
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "slug": self.slug,
            "organization_id": self.organization_id,
            "status": self.status.value,
            "edition": self.edition,
            "region": self.region,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True, slots=True)
class OrganizationTenantBinding:
    """Declares ownership without any synchronization or persistence."""

    organization_id: str
    tenant_id: str


@dataclass(frozen=True, slots=True)
class TenantMembershipDescriptor:
    """Membership scope descriptor that grants no tenant access automatically."""

    tenant_id: str
    membership_id: str
    workspace_id: str | None = None


@dataclass(frozen=True, slots=True)
class TenantAccessDescriptor:
    """Requested scope descriptor that makes no authorization decision."""

    tenant_id: str
    principal_id: str
    requested_scopes: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_scopes", frozenset(self.requested_scopes))
