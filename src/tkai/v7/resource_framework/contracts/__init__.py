"""Immutable contracts for the V7 Unified Resource Management Framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, cast

from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ResourceType(str, Enum):
    ACCOUNT = "account"
    BROWSER = "browser"
    BROWSER_PROFILE = "browser_profile"
    DEVICE = "device"
    PROXY = "proxy"
    WORKER = "worker"
    QUEUE = "queue"
    STORAGE = "storage"
    SCHEDULER = "scheduler"
    WORKFLOW = "workflow"
    CAPABILITY = "capability"
    SERVICE = "service"
    EXTENSION = "extension"
    MODULE = "module"


class ResourceLifecycle(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    AVAILABLE = "available"
    RESERVED = "reserved"
    PLANNED = "planned"
    UNAVAILABLE = "unavailable"
    PAUSED = "paused"
    RECOVERING = "recovering"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class ResourceScope:
    tenant_reference: str
    workspace_reference: str


@dataclass(frozen=True)
class Capacity:
    total: float = 1.0
    used: float = 0.0
    reserved: float = 0.0
    unit: str = "slot"

    @property
    def available(self) -> float:
        return max(0.0, self.total - self.used - self.reserved)

    @property
    def utilization(self) -> float:
        return 0.0 if self.total <= 0 else (self.used + self.reserved) / self.total


@dataclass(frozen=True)
class Availability:
    available: bool = True
    quantity: float = 1.0
    reason: str | None = None
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class DependencyReference:
    resource_id: str
    required_version: str | None = None
    optional: bool = False


@dataclass(frozen=True)
class ResourceConstraint:
    name: str
    satisfied: bool = True
    reference: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", filter_secrets(self.details))


@dataclass(frozen=True)
class ResourceHealth:
    status: str = "unknown"
    ready: bool = False
    message: str | None = None
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class Resource:
    resource_id: str
    resource_type: str
    category: str
    owner: str
    version: str
    scope: ResourceScope
    state: Mapping[str, object] = field(default_factory=dict)
    capacity: Capacity = field(default_factory=Capacity)
    availability: Availability = field(default_factory=Availability)
    reservation_reference: str | None = None
    dependency_references: tuple[DependencyReference, ...] = ()
    constraints: tuple[ResourceConstraint, ...] = ()
    lifecycle: ResourceLifecycle = ResourceLifecycle.REGISTERED
    health: ResourceHealth = field(default_factory=ResourceHealth)
    metrics: Mapping[str, float] = field(default_factory=dict)
    audit: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()
    tags: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        required = (
            self.resource_id,
            self.resource_type,
            self.category,
            self.owner,
            self.version,
            self.scope.tenant_reference,
            self.scope.workspace_reference,
        )
        if not all(required):
            raise ValueError(
                "resource identity, type, owner, version, and scope required"
            )
        object.__setattr__(self, "state", filter_secrets(self.state))
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))
        object.__setattr__(
            self, "resource_type", self.resource_type.strip().lower().replace(" ", "_")
        )


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    resource_id: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationReport:
    resource_id: str
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class CapacityAnalysis:
    resource_id: str
    total: float
    utilized: float
    reserved: float
    available: float
    utilization_estimate: float
    availability_estimate: float
    reservation_estimate: float
    growth_estimate: float
    historical_trend_references: tuple[str, ...] = ()
    advisory_only: bool = True
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class Reservation:
    reservation_id: str
    resource_id: str
    quantity: float
    owner: str
    scope: ResourceScope
    expires_at: str | None = None
    reference: str | None = None
    status: str = "active"
    reference_only: bool = True
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ReservationConflict:
    resource_id: str
    requested: float
    available: float
    conflicting_reservation_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class AllocationPlan:
    plan_id: str
    resource_id: str
    ordered_resource_ids: tuple[str, ...]
    requested_capacity: float
    ready: bool
    bounded: bool
    conflicts: tuple[str, ...] = ()
    reservation_references: tuple[str, ...] = ()
    advisory_only: bool = True
    runtime_allocation_enabled: bool = False
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_id: str
    resource_id: str
    strategy: str
    target_reference: str
    ready: bool
    rollback: bool = False
    coordinated: bool = True
    reference_only: bool = True
    issues: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class AuditEntry:
    entry_id: str
    resource_id: str
    category: str
    action: str
    actor: str
    reference: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(self, "details", filter_secrets(self.details))


@dataclass(frozen=True)
class ResourceTypeContract:
    """Extensible metadata contract for built-in and future resource types."""

    name: str
    schema_version: str = "1.0.0"
    capabilities: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("resource type contract name is required")
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


def serialize(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "AllocationPlan",
    "AuditEntry",
    "Availability",
    "Capacity",
    "CapacityAnalysis",
    "DependencyReference",
    "RecoveryPlan",
    "Reservation",
    "ReservationConflict",
    "Resource",
    "ResourceConstraint",
    "ResourceHealth",
    "ResourceLifecycle",
    "ResourceScope",
    "ResourceType",
    "ResourceTypeContract",
    "ValidationIssue",
    "ValidationReport",
    "serialize",
    "utc_now",
)
