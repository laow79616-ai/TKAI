"""Immutable contracts for the V10 Sovereign Recovery Mesh."""

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


class RecoveryStrategyType(str, Enum):
    MANUAL_RECOVERY = "manual_recovery"
    ASSISTED_RECOVERY = "assisted_recovery"
    DEFERRED_RECOVERY = "deferred_recovery"
    REVIEW_REQUIRED = "review_required"
    UNSUPPORTED = "unsupported"


class RecoveryPlanStatus(str, Enum):
    DRAFT = "draft"
    CANDIDATE = "candidate"
    APPROVED_REFERENCE = "approved_reference"
    DEFERRED = "deferred"
    ARCHIVED = "archived"


class RecoveryReadinessStatus(str, Enum):
    READY = "ready"
    CONDITIONALLY_READY = "conditionally_ready"
    REVIEW_REQUIRED = "review_required"
    NOT_READY = "not_ready"
    UNKNOWN = "unknown"


class RecoveryValidationType(str, Enum):
    DEPENDENCY = "dependency_validation"
    COMPATIBILITY = "compatibility_validation"
    GOVERNANCE = "governance_validation"
    INTEGRITY = "integrity_validation"
    TRUST = "trust_validation"
    OPERATIONAL = "operational_validation"


@dataclass(frozen=True)
class RecoveryProfile:
    recovery_profile_id: str
    subject_reference: str
    context_references: tuple[str, ...] = ()
    strategy_references: tuple[str, ...] = ()
    recovery_plan_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    readiness_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    operations_references: tuple[str, ...] = ()
    planning_references: tuple[str, ...] = ()
    decision_references: tuple[str, ...] = ()
    reasoning_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=_metrics)
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class RecoveryContext:
    context_id: str
    subject_reference: str
    summary: str = ""
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class RecoveryStrategy:
    strategy_id: str
    subject_reference: str
    strategy_type: RecoveryStrategyType
    context_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_plan_id: str
    subject_reference: str
    status: RecoveryPlanStatus = RecoveryPlanStatus.DRAFT
    strategy_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class RecoveryDependency:
    dependency_id: str
    subject_reference: str
    required_references: tuple[str, ...] = ()
    status: str = "unknown"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class RecoveryReadiness:
    readiness_id: str
    subject_reference: str
    status: RecoveryReadinessStatus = RecoveryReadinessStatus.UNKNOWN
    validation_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)
    triggers_recovery: bool = field(default=False, init=False)


@dataclass(frozen=True)
class RecoveryValidation:
    validation_id: str
    subject_reference: str
    validation_type: RecoveryValidationType
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
    "RecoveryContext",
    "RecoveryDependency",
    "RecoveryPlan",
    "RecoveryPlanStatus",
    "RecoveryProfile",
    "RecoveryReadiness",
    "RecoveryReadinessStatus",
    "RecoveryStrategy",
    "RecoveryStrategyType",
    "RecoveryValidation",
    "RecoveryValidationType",
    "Reference",
)
