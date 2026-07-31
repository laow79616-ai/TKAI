"""Immutable contracts for the V10 Sovereign Operations Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


def _metadata() -> Mapping[str, object]:
    return MappingProxyType({})


def _metrics() -> Mapping[str, float]:
    return MappingProxyType({})


class OperationalStatus(str, Enum):
    READY = "ready"
    CONDITIONALLY_READY = "conditionally_ready"
    MAINTENANCE = "maintenance"
    DEGRADED_REFERENCE = "degraded_reference"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    LIMITED = "limited"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class AssessmentType(str, Enum):
    READINESS = "readiness"
    CAPACITY = "capacity"
    AVAILABILITY = "availability"
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    TRUST = "trust"
    GOVERNANCE = "governance"
    SECURITY = "security"
    DEPLOYMENT_REFERENCE = "deployment_reference"
    RUNTIME_REFERENCE = "runtime_reference"


@dataclass(frozen=True)
class OperationsProfile:
    operations_profile_id: str
    subject_reference: str
    context_references: tuple[str, ...] = ()
    operational_references: tuple[str, ...] = ()
    readiness_references: tuple[str, ...] = ()
    maintenance_references: tuple[str, ...] = ()
    capacity_references: tuple[str, ...] = ()
    availability_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    assessment_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    planning_references: tuple[str, ...] = ()
    decision_references: tuple[str, ...] = ()
    reasoning_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=_metrics)
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class OperationalContext:
    context_id: str
    subject_reference: str
    summary: str = ""
    scope: Scope = field(default_factory=Scope)
    audit_reference: str | None = None
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class OperationReference:
    operation_id: str
    subject_reference: str
    status: OperationalStatus = OperationalStatus.UNKNOWN
    context_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    audit_reference: str | None = None
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Readiness:
    readiness_id: str
    subject_reference: str
    status: OperationalStatus = OperationalStatus.UNKNOWN
    validation_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Maintenance:
    maintenance_id: str
    subject_reference: str
    status: OperationalStatus = OperationalStatus.MAINTENANCE
    maintenance_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)
    schedulable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Capacity:
    capacity_id: str
    subject_reference: str
    capacity_reference: str
    utilization_reference: str | None = None
    limits: Mapping[str, float] = field(default_factory=_metrics)
    thresholds: Mapping[str, float] = field(default_factory=_metrics)
    warnings: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)
    allocates_resources: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Availability:
    availability_id: str
    subject_reference: str
    status: AvailabilityStatus = AvailabilityStatus.UNKNOWN
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)
    repairs_health: bool = field(default=False, init=False)


@dataclass(frozen=True)
class OperationalAssessment:
    assessment_id: str
    subject_reference: str
    assessment_type: AssessmentType
    status: str = "unknown"
    evidence_references: tuple[str, ...] = ()
    deployment_reference: str | None = None
    runtime_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class OperationsValidation:
    validation_id: str
    subject_reference: str
    status: str = "unknown"
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Reference:
    reference_id: str
    mesh: str
    subject_reference: str
    generation: str = "v10"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


__all__ = (
    "AssessmentType",
    "Availability",
    "AvailabilityStatus",
    "Capacity",
    "Maintenance",
    "OperationalAssessment",
    "OperationalContext",
    "OperationalStatus",
    "OperationReference",
    "OperationsProfile",
    "OperationsValidation",
    "Readiness",
    "Reference",
)
