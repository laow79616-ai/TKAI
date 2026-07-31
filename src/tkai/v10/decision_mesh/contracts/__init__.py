"""Immutable metadata contracts for the V10 Sovereign Decision Mesh."""

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


class OptionStatus(str, Enum):
    CANDIDATE = "candidate"
    PREFERRED = "preferred"
    CONDITIONAL = "conditional"
    REJECTED = "rejected"
    DEFERRED = "deferred"
    UNKNOWN = "unknown"


class CriterionType(str, Enum):
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    TRUST = "trust"
    GOVERNANCE = "governance"
    SECURITY = "security"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    API = "api"
    DEPLOYMENT = "deployment"
    MAINTAINABILITY = "maintainability"
    OPERATIONAL_COMPLEXITY = "operational_complexity"
    DOCUMENTATION_QUALITY = "documentation_quality"
    TEST_COVERAGE = "test_coverage"
    RISK = "risk"


class RecommendationStatus(str, Enum):
    RECOMMENDED = "recommended"
    CONDITIONALLY_RECOMMENDED = "conditionally_recommended"
    REVIEW_REQUIRED = "review_required"
    NOT_RECOMMENDED = "not_recommended"


class LimitationType(str, Enum):
    MISSING_EVIDENCE = "missing_evidence"
    COMPATIBILITY_GAP = "compatibility_gap"
    INTEGRITY_GAP = "integrity_gap"
    TRUST_GAP = "trust_gap"
    GOVERNANCE_GAP = "governance_gap"
    UNKNOWN = "unknown"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class DecisionProfile:
    profile_id: str
    subject_reference: str
    context_references: tuple[str, ...] = ()
    option_references: tuple[str, ...] = ()
    evaluation_references: tuple[str, ...] = ()
    criteria_references: tuple[str, ...] = ()
    tradeoff_references: tuple[str, ...] = ()
    risk_references: tuple[str, ...] = ()
    dependency_references: tuple[str, ...] = ()
    recommendation_references: tuple[str, ...] = ()
    confidence_references: tuple[str, ...] = ()
    limitation_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    reasoning_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=_metrics)
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class DecisionContext:
    context_id: str
    subject_reference: str
    context_scope: str
    tenant_reference: str = ""
    workspace_reference: str = ""
    namespace: str = "default"
    time_range: tuple[str, str] | None = None
    version: str = "10.0.0"
    status: str = "registered"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    subject_reference: str
    summary: str
    status: OptionStatus = OptionStatus.UNKNOWN
    dependency_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class EvaluationCriterion:
    criterion_id: str
    criterion_type: CriterionType
    summary: str = ""
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    option_references: tuple[str, ...]
    criteria_references: tuple[str, ...]
    evidence_references: tuple[str, ...] = ()
    confidence: float | None = None
    limitations: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Tradeoff:
    tradeoff_id: str
    benefit: str = ""
    cost: str = ""
    risk: str = ""
    complexity: str = ""
    compatibility_impact: str = "unknown"
    security_impact: str = "unknown"
    governance_impact: str = "unknown"
    integrity_impact: str = "unknown"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Risk:
    risk_id: str
    summary: str
    severity: str = "unknown"
    likelihood: str = "unknown"
    evidence_references: tuple[str, ...] = ()
    limitation_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    subject_reference: str
    dependency_reference: str
    status: str = "unknown"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    option_references: tuple[str, ...]
    status: RecommendationStatus
    summary: str = ""
    confidence_reference: str | None = None
    limitation_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    advisory_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class DecisionConfidence:
    confidence_id: str
    value: float | None
    band: str
    evidence_summary: str
    explanation: str
    limitation_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    explainable_metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Limitation:
    limitation_id: str
    limitation_type: LimitationType
    summary: str
    reference_ids: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Reference:
    reference_id: str
    mesh: str
    subject_reference: str
    generation: str = "v10"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


__all__ = (
    "CriterionType",
    "DecisionConfidence",
    "DecisionContext",
    "DecisionOption",
    "DecisionProfile",
    "Dependency",
    "Evaluation",
    "EvaluationCriterion",
    "Limitation",
    "LimitationType",
    "OptionStatus",
    "Recommendation",
    "RecommendationStatus",
    "Reference",
    "Risk",
    "Tradeoff",
)
