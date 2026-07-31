"""Immutable metadata contracts for the V10 Sovereign Planning Mesh."""

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


class ObjectiveStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    APPROVED_REFERENCE = "approved_reference"
    DEFERRED = "deferred"
    COMPLETED_REFERENCE = "completed_reference"
    ARCHIVED = "archived"


class TimelineStatus(str, Enum):
    PLANNED = "planned"
    ESTIMATED = "estimated"
    TENTATIVE = "tentative"
    DEFERRED = "deferred"
    UNKNOWN = "unknown"


class DependencyType(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    API = "api"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"


class ReadinessStatus(str, Enum):
    READY = "ready"
    CONDITIONALLY_READY = "conditionally_ready"
    REVIEW_REQUIRED = "review_required"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


class ValidationType(str, Enum):
    OBJECTIVE = "objective_validation"
    MILESTONE = "milestone_validation"
    DEPENDENCY = "dependency_validation"
    TIMELINE = "timeline_validation"
    RISK = "risk_validation"
    COMPATIBILITY = "compatibility_validation"
    GOVERNANCE = "governance_validation"
    INTEGRITY = "integrity_validation"
    TRUST = "trust_validation"
    DECISION = "decision_validation"
    REASONING = "reasoning_validation"
    KNOWLEDGE = "knowledge_validation"


@dataclass(frozen=True)
class PlanningProfile:
    profile_id: str
    subject_reference: str
    context_references: tuple[str, ...] = ()
    objective_references: tuple[str, ...] = ()
    milestone_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    timeline_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    risk_references: tuple[str, ...] = ()
    alternative_references: tuple[str, ...] = ()
    readiness_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    decision_references: tuple[str, ...] = ()
    reasoning_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=_metrics)
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class PlanningContext:
    context_id: str
    subject_reference: str
    summary: str = ""
    tenant_reference: str = ""
    workspace_reference: str = ""
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Objective:
    objective_id: str
    subject_reference: str
    summary: str
    status: ObjectiveStatus = ObjectiveStatus.DRAFT
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Milestone:
    milestone_id: str
    objective_reference: str
    dependency_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    readiness_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Timeline:
    timeline_id: str
    subject_reference: str
    status: TimelineStatus = TimelineStatus.UNKNOWN
    start_reference: str | None = None
    end_reference: str | None = None
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    subject_reference: str
    dependency_reference: str
    dependency_type: DependencyType
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class PlanningReadiness:
    readiness_id: str
    subject_reference: str
    status: ReadinessStatus = ReadinessStatus.UNKNOWN
    validation_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class PlanningValidation:
    validation_id: str
    subject_reference: str
    validation_type: ValidationType
    status: str = "unknown"
    evidence_references: tuple[str, ...] = ()
    audit_reference: str | None = None
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
    "Dependency",
    "DependencyType",
    "Milestone",
    "Objective",
    "ObjectiveStatus",
    "PlanningContext",
    "PlanningProfile",
    "PlanningReadiness",
    "PlanningValidation",
    "ReadinessStatus",
    "Reference",
    "Timeline",
    "TimelineStatus",
    "ValidationType",
)
