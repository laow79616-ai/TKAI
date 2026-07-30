"""Immutable contracts for advisory cross-framework operations metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


class OperationsLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    REVIEWED = "reviewed"
    READY_REFERENCE = "ready-reference"
    DEGRADED = "degraded"
    ARCHIVED = "archived"


class ReadinessKind(str, Enum):
    WORKFLOW = "workflow"
    CAPABILITY = "capability"
    RESOURCE = "resource"
    RUNTIME = "runtime"
    RECOVERY = "recovery"
    GOVERNANCE = "governance"
    COMPATIBILITY = "compatibility"


class DependencyKind(str, Enum):
    FRAMEWORK = "framework"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    RUNTIME = "runtime"
    GOVERNANCE = "governance"
    COMPATIBILITY = "compatibility"


@dataclass(frozen=True)
class OperationsScope:
    tenant: str = "default"
    workspace: str = "default"
    operations: str = "default"


@dataclass(frozen=True)
class OperationsReference:
    identifier: str
    version: str = ""
    generation: str = ""
    kind: str = "metadata"
    uri: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        generation = self.generation.lower()
        if generation not in {"", "v6", "v7", "v8"}:
            raise ValueError("reference generation must be V6, V7, or V8")
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class OperationProfile:
    profile_id: str
    version: str
    owner: str
    operation_references: tuple[OperationsReference, ...] = ()
    workflow_references: tuple[OperationsReference, ...] = ()
    resource_references: tuple[OperationsReference, ...] = ()
    runtime_references: tuple[OperationsReference, ...] = ()
    readiness_references: tuple[OperationsReference, ...] = ()
    governance_references: tuple[OperationsReference, ...] = ()
    compatibility_references: tuple[OperationsReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: OperationsScope = OperationsScope()
    lifecycle: OperationsLifecycle = OperationsLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def execution_eligible(self) -> bool:
        return False


@dataclass(frozen=True)
class ReadinessMetadata:
    readiness_id: str
    kind: ReadinessKind
    subject: OperationsReference
    ready: bool = False
    status: str = "unknown"
    evidence_references: tuple[OperationsReference, ...] = ()
    blockers: tuple[str, ...] = ()
    checked_at: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.readiness_id:
            raise ValueError("readiness_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def authorizes_execution(self) -> bool:
        return False


@dataclass(frozen=True)
class SummaryMetadata:
    summary_id: str
    summary_type: str
    subject: OperationsReference
    status: str = "unknown"
    dependency_references: tuple[OperationsReference, ...] = ()
    version_history: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        supported = {
            "operation",
            "workflow",
            "runtime",
            "dependency",
            "resource",
            "recovery",
        }
        if not self.summary_id or self.summary_type not in supported:
            raise ValueError("summary_id and supported summary_type are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class DependencyMetadata:
    dependency_id: str
    kind: DependencyKind
    source: OperationsReference
    target: OperationsReference
    required: bool = True
    available: bool = False
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.dependency_id:
            raise ValueError("dependency_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class CapacityMetadata:
    capacity_id: str
    subject: OperationsReference
    capacity: float = 0
    availability: float = 0
    utilization: float = 0
    reservation: float = 0
    forecast_references: tuple[OperationsReference, ...] = ()
    unit: str = "units"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.capacity_id:
            raise ValueError("capacity_id is required")
        if (
            min(self.capacity, self.availability, self.utilization, self.reservation)
            < 0
        ):
            raise ValueError("capacity values cannot be negative")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def allocated(self) -> bool:
        return False


@dataclass(frozen=True)
class RecoveryMetadata:
    recovery_id: str
    subject: OperationsReference
    status: str = "unknown"
    rollback_references: tuple[OperationsReference, ...] = ()
    readiness_references: tuple[OperationsReference, ...] = ()
    compatibility_references: tuple[OperationsReference, ...] = ()
    governance_references: tuple[OperationsReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.recovery_id:
            raise ValueError("recovery_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def performs_rollback(self) -> bool:
        return False


@dataclass(frozen=True)
class CompatibilityMetadata:
    compatibility_id: str
    source: OperationsReference
    target: OperationsReference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.compatibility_id:
            raise ValueError("compatibility_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class HealthMetadata:
    health_id: str
    subject: OperationsReference
    status: str = "unknown"
    checks: Mapping[str, object] = field(default_factory=immutable_metadata)
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.health_id:
            raise ValueError("health_id is required")
        object.__setattr__(self, "checks", immutable_metadata(self.checks))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class MetricMetadata:
    metric_id: str
    name: str
    value: float
    unit: str = ""
    subject: OperationsReference | None = None
    trace_reference: OperationsReference | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.metric_id or not self.name:
            raise ValueError("metric_id and name are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


Reference = OperationsReference

__all__ = (
    "CapacityMetadata",
    "CompatibilityMetadata",
    "DependencyKind",
    "DependencyMetadata",
    "HealthMetadata",
    "MetricMetadata",
    "OperationProfile",
    "OperationsLifecycle",
    "OperationsReference",
    "OperationsScope",
    "ReadinessKind",
    "ReadinessMetadata",
    "RecoveryMetadata",
    "Reference",
    "SummaryMetadata",
    "immutable_metadata",
)
