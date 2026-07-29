"""Immutable, secret-safe contracts for V7 intelligence and decisions."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_metadata(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    data = dict(value or {})
    blocked = ("password", "secret", "token", "cookie", "session", "api_key",
               "proxy", "chain_of_thought", "hidden_reasoning")
    for key, item in data.items():
        if any(word in key.lower() for word in blocked):
            raise ValueError(f"unsafe metadata field: {key}")
        if isinstance(item, (dict, list, tuple, set)) or len(str(item)) > 512:
            raise ValueError("safe metadata values must be bounded scalars")
    return MappingProxyType(data)


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    COLLECTING = "collecting"
    VALIDATING = "validating"
    ANALYZING = "analyzing"
    READY = "ready"
    UNDER_REVIEW = "under-review"
    APPROVED_REFERENCE = "approved-reference"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class Scope:
    tenant: str
    workspace: str
    namespace: str = "intelligence"

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.namespace)):
            raise ValueError("tenant, workspace, and namespace are required")
        if any(len(x) > 128 for x in (self.tenant, self.workspace, self.namespace)):
            raise ValueError("scope value is too long")


@dataclass(frozen=True)
class VersionMetadata:
    version: int = 1
    effective_date: datetime = field(default_factory=utc_now)
    superseded_by: str | None = None
    change_reason: str = "initial"
    change_history: tuple[str, ...] = ()
    deprecation_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)


@dataclass(frozen=True)
class IntelligenceProfile:
    profile_id: str
    name: str
    description: str
    owner: str
    scope: Scope
    time_horizon: str
    source_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.DRAFT
    version: int = 1
    health: str = "unknown"
    metrics: Mapping[str, Any] = field(default_factory=safe_metadata)
    audit_reference: str | None = None
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    @property
    def namespace(self) -> str:
        return self.scope.namespace

    @property
    def tenant_reference(self) -> str:
        return self.scope.tenant

    @property
    def workspace_reference(self) -> str:
        return self.scope.workspace

    def __post_init__(self) -> None:
        object.__setattr__(self, "metrics", safe_metadata(self.metrics))
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class IntelligenceContext:
    context_id: str
    profile_reference: str
    context_type: str
    subject_reference: str
    time_range: tuple[datetime, datetime]
    scope: Scope
    source_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    version: int = 1
    integrity_status: str = "unverified"
    metadata: Mapping[str, Any] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        start, end = self.time_range
        if start > end or (end - start).days > 3660:
            raise ValueError("invalid or unbounded time range")
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class SourceAdapter:
    source_id: str
    name: str
    version: str
    read_only: bool = True
    local_only: bool = True
    max_results: int = 100

    def __post_init__(self) -> None:
        if (
            not self.read_only
            or not self.local_only
            or not 1 <= self.max_results <= 1000
        ):
            raise ValueError("source adapters must be bounded, read-only, and local")


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    source_reference: str
    subject_reference: str
    time_range: tuple[datetime, datetime]
    payload_reference: str
    payload_hash: str
    integrity_status: str
    reliability: float
    relevance: float
    freshness: float
    provenance: str
    validation_status: str
    scope: Scope
    version: int = 1
    audit_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        if not self.payload_reference.startswith(("ref://", "data://", "storage://",
                                                  "v6://", "v7://")):
            raise ValueError("evidence payloads must be reference-only")
        if len(self.payload_hash) < 32:
            raise ValueError("payload integrity hash is required")
        if any(not 0 <= x <= 1 for x in (self.reliability, self.relevance,
                                         self.freshness)):
            raise ValueError("evidence scores must be between zero and one")
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class KnowledgeReference:
    knowledge_reference: str
    knowledge_version: int
    source_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    confidence: float
    validity_window: tuple[datetime, datetime]
    compatibility_metadata: Mapping[str, Any]
    scope: Scope
    superseded_by: str | None = None
    integrity_status: str = "unverified"


@dataclass(frozen=True)
class Signal:
    signal_id: str
    signal_type: str
    source: str
    subject: str
    timestamp: datetime
    direction: str
    magnitude_metadata: Mapping[str, Any]
    confidence: float
    evidence_references: tuple[str, ...]
    risk_classification: str
    scope: Scope
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    audit_reference: str | None = None


@dataclass(frozen=True)
class Observation:
    observation_id: str
    context_reference: str
    signal_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    description: str
    classification: str
    confidence: float
    validation_status: str
    timestamp: datetime
    scope: Scope
    version: int = 1
    is_fact: bool = False
    is_causal_conclusion: bool = False

    def __post_init__(self) -> None:
        if self.is_fact or self.is_causal_conclusion:
            raise ValueError("observations are not facts or causal conclusions")


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    description: str
    context_reference: str
    evidence_for: tuple[str, ...]
    evidence_against: tuple[str, ...]
    assumptions: tuple[str, ...]
    confidence: float
    falsification_criteria: tuple[str, ...]
    validation_status: str
    risk_if_incorrect: str
    scope: Scope
    version: int = 1
    lifecycle: Lifecycle = Lifecycle.DRAFT
    established_fact: bool = False

    def __post_init__(self) -> None:
        if self.established_fact or not self.falsification_criteria:
            raise ValueError("hypotheses require falsification and are not facts")


@dataclass(frozen=True)
class EvaluationScore:
    score: float
    factors: tuple[str, ...]
    weight_metadata: Mapping[str, Any]
    supporting_references: tuple[str, ...]
    limitations: tuple[str, ...]
    explanation_summary: str

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1 or not self.factors or not self.explanation_summary:
            raise ValueError("an explainable bounded score is required")


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    evaluation_type: str
    subject_reference: str
    result: EvaluationScore
    scope: Scope
    version: int = 1


@dataclass(frozen=True)
class ConfidenceCalibration:
    original_confidence: float
    evidence_adjusted_confidence: float
    policy_adjusted_confidence: float
    risk_adjusted_confidence: float
    calibrated_confidence: float
    confidence_interval_metadata: Mapping[str, Any]
    calibration_reference: str | None
    historical_accuracy_reference: str | None
    confidence_explanation: str
    limitations: tuple[str, ...]

    def __post_init__(self) -> None:
        values = (self.original_confidence, self.evidence_adjusted_confidence,
                  self.policy_adjusted_confidence, self.risk_adjusted_confidence,
                  self.calibrated_confidence)
        if any(not 0 <= x <= 1 for x in values):
            raise ValueError("confidence values must be between zero and one")


@dataclass(frozen=True)
class Alternative:
    alternative_id: str
    decision_reference: str
    name: str
    description: str
    expected_outcome_reference: str | None
    benefits: tuple[str, ...]
    risks: tuple[str, ...]
    constraints: tuple[str, ...]
    resource_references: tuple[str, ...]
    schedule_references: tuple[str, ...]
    recovery_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    confidence: float
    scope: Scope
    evaluation_reference: str | None = None
    version: int = 1


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    recommendation_type: str
    subject_reference: str
    summary: str
    evidence_references: tuple[str, ...]
    confidence: float
    scope: Scope
    limitations: tuple[str, ...] = ()
    executable: bool = False
    version: int = 1

    def __post_init__(self) -> None:
        if self.executable:
            raise ValueError("recommendations are advisory and non-executable")


@dataclass(frozen=True)
class DecisionRecord:
    decision_id: str
    profile_reference: str
    context_reference: str
    decision_type: str
    objective_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    knowledge_references: tuple[str, ...]
    alternative_references: tuple[str, ...]
    constraint_references: tuple[str, ...]
    policy_references: tuple[str, ...]
    risk_references: tuple[str, ...]
    recommendation_references: tuple[str, ...]
    confidence: float
    status: str
    scope: Scope
    version: int = 1
    created_at: datetime = field(default_factory=utc_now)
    review_reference: str | None = None
    approval_reference: str | None = None
    audit_reference: str | None = None
    advisory_only: bool = True
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.advisory_only or self.execution_authorized:
            raise ValueError("decisions cannot authorize execution")


@dataclass(frozen=True)
class ReasoningMetadata:
    reasoning_session_id: str
    profile_reference: str
    context_reference: str
    evidence_references: tuple[str, ...]
    knowledge_references: tuple[str, ...]
    observation_references: tuple[str, ...]
    hypothesis_references: tuple[str, ...]
    evaluation_references: tuple[str, ...]
    confidence: float
    explanation_reference: str | None
    trace_reference: str | None
    policy_references: tuple[str, ...]
    lifecycle: Lifecycle
    scope: Scope
    version: int = 1
    audit_reference: str | None = None
    summary: str = ""

    def __post_init__(self) -> None:
        blocked = ("chain-of-thought", "hidden reasoning")
        if any(value in self.summary.lower() for value in blocked):
            raise ValueError("hidden reasoning storage is prohibited")


@dataclass(frozen=True)
class Explanation:
    explanation_id: str
    decision_summary: str
    recommendation_summary: str
    evidence_used: tuple[str, ...]
    evidence_missing: tuple[str, ...]
    sources_used: tuple[str, ...]
    assumptions: tuple[str, ...]
    constraints: tuple[str, ...]
    policies_applied: tuple[str, ...]
    risks_considered: tuple[str, ...]
    alternatives_considered: tuple[str, ...]
    confidence_explanation: str
    evaluation_breakdown: tuple[str, ...]
    limitations: tuple[str, ...]
    review_requirements: tuple[str, ...]
    scope: Scope
    version: int = 1


@dataclass(frozen=True)
class Review:
    review_id: str
    review_type: str
    reviewer: str
    review_scope: str
    findings: tuple[str, ...]
    required_changes: tuple[str, ...]
    advisory_recommendations: tuple[str, ...]
    status: str
    timestamp: datetime
    scope: Scope
    audit_reference: str | None = None


@dataclass(frozen=True)
class Approval:
    approval_id: str
    artifact_reference: str
    artifact_version: int
    approval_scope: str
    approver: str
    decision: str
    conditions: tuple[str, ...]
    expiry: datetime | None
    timestamp: datetime
    scope: Scope
    audit_reference: str | None = None
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized:
            raise ValueError("artifact approval never authorizes execution")


@dataclass(frozen=True)
class Comparison:
    comparison_id: str
    comparison_type: str
    left_reference: str
    right_reference: str
    factors: tuple[str, ...]
    result_summary: str
    scope: Scope


@dataclass(frozen=True)
class GovernanceMetadata:
    governance_id: str
    policy_references: tuple[str, ...]
    governance_constraints: tuple[str, ...]
    review_requirements: tuple[str, ...]
    approval_requirements: tuple[str, ...]
    risk_thresholds: Mapping[str, Any]
    pause_aware: bool
    kill_switch_aware: bool
    audit_requirements: tuple[str, ...]
    scope: Scope


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(k): serialize(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [serialize(v) for v in value]
    if hasattr(value, "__dataclass_fields__"):
        return serialize(asdict(value))
    return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
