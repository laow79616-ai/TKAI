"""Immutable contracts for the V9 Adaptive Reasoning Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

FORBIDDEN_KEYS = frozenset(
    {
        "chain_of_thought",
        "hidden_reasoning",
        "internal_reasoning",
        "internal_scratchpad",
        "private_deliberation",
        "raw_reasoning_trace",
    }
)


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


def validate_safe_metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    def walk(value: object) -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                if (
                    str(key).lower().replace("-", "_").replace(" ", "_")
                    in FORBIDDEN_KEYS
                ):
                    raise ValueError(
                        "hidden reasoning and internal scratchpads are prohibited"
                    )
                walk(item)
        elif isinstance(value, (tuple, list)):
            for item in value:
                walk(item)

    walk(values)
    return immutable_metadata(values)


class ReasoningLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    FEDERATING = "federating"
    COLLECTING_EVIDENCE = "collecting_evidence"
    VALIDATING = "validating"
    EVALUATING = "evaluating"
    READY = "ready"
    UNDER_REVIEW = "under_review"
    APPROVED_REFERENCE = "approved_reference"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class ReasoningScope:
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "default"
    profile: str = "*"
    context: str = "*"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(c.isspace() for c in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", validate_safe_metadata(self.metadata))


def _scores(**values: float) -> None:
    for name, value in values.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class Profile:
    profile_id: str
    name: str
    description: str
    version: str
    owner: str
    namespace: str = "default"
    tenant_reference: Reference | None = None
    workspace_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()
    time_horizon: tuple[str, str] = ("", "")
    context_references: tuple[Reference, ...] = ()
    source_references: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    signal_references: tuple[Reference, ...] = ()
    observation_references: tuple[Reference, ...] = ()
    hypothesis_references: tuple[Reference, ...] = ()
    evaluation_references: tuple[Reference, ...] = ()
    recommendation_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    lifecycle: ReasoningLifecycle = ReasoningLifecycle.DRAFT
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    tags: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not all((self.profile_id, self.name, self.version, self.owner)):
            raise ValueError("profile_id, name, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(
            self, "safe_metadata", validate_safe_metadata(self.safe_metadata)
        )
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class Context:
    context_id: str
    profile_reference: Reference
    context_type: str
    subject_reference: Reference
    tenant_scope: str = "default"
    workspace_scope: str = "default"
    namespace: str = "default"
    time_range: tuple[str, str] = ("", "")
    source_references: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    policy_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    integrity_status: str = "unverified"
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "safe_metadata", validate_safe_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class Source:
    source_id: str
    source_type: str
    framework_reference: Reference
    module_reference: Reference | None = None
    version: str = ""
    availability: str = "unknown"
    reliability: float = 0.0
    freshness: float = 0.0
    integrity_status: str = "unverified"
    compatibility_status: str = "unknown"
    governance_status: str = "unknown"
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(reliability=self.reliability, freshness=self.freshness)


@dataclass(frozen=True)
class KnowledgeRecord:
    knowledge_reference: Reference
    knowledge_version: str = ""
    domain_references: tuple[Reference, ...] = ()
    concept_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    provenance_reference: Reference | None = None
    lineage_reference: Reference | None = None
    confidence: float = 0.0
    validity_window: tuple[str, str] = ("", "")
    compatibility_status: str = "unknown"
    integrity_status: str = "unverified"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(confidence=self.confidence)


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    source_reference: Reference
    subject_reference: Reference
    time_range: tuple[str, str] = ("", "")
    payload_reference: Reference | None = None
    payload_hash: str = ""
    provenance_reference: Reference | None = None
    lineage_reference: Reference | None = None
    reliability: float = 0.0
    relevance: float = 0.0
    freshness: float = 0.0
    integrity_status: str = "unverified"
    validation_status: str = "pending"
    confidence: float = 0.0
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(
            reliability=self.reliability,
            relevance=self.relevance,
            freshness=self.freshness,
            confidence=self.confidence,
        )
        object.__setattr__(
            self, "safe_metadata", validate_safe_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class Signal:
    signal_id: str
    signal_type: str
    source_reference: Reference
    subject_reference: Reference
    direction: str = "neutral"
    magnitude_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    timestamp: str = ""
    evidence_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    risk_classification: str = "unknown"
    compatibility_status: str = "unknown"
    lifecycle: ReasoningLifecycle = ReasoningLifecycle.DRAFT
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(confidence=self.confidence)
        object.__setattr__(
            self, "magnitude_metadata", validate_safe_metadata(self.magnitude_metadata)
        )


@dataclass(frozen=True)
class Observation:
    observation_id: str
    context_reference: Reference
    description: str
    signal_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    classification: str = "observation"
    confidence: float = 0.0
    validation_status: str = "pending"
    limitations: tuple[str, ...] = ()
    timestamp: str = ""
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if self.classification.lower() in {"fact", "causal_conclusion"}:
            raise ValueError(
                "observations must be distinguished from facts and causality"
            )
        _scores(confidence=self.confidence)


@dataclass(frozen=True)
class Hypothesis:
    hypothesis_id: str
    description: str
    context_reference: Reference
    evidence_for: tuple[Reference, ...] = ()
    evidence_against: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    assumption_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    falsification_criteria: tuple[str, ...] = ()
    validation_status: str = "pending"
    risk_if_incorrect: str = ""
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    lifecycle: ReasoningLifecycle = ReasoningLifecycle.DRAFT
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()
    classification: str = "hypothesis"

    def __post_init__(self) -> None:
        if self.classification != "hypothesis":
            raise ValueError("hypotheses must always be labeled as hypotheses")
        _scores(confidence=self.confidence)


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    description: str
    source_reference: Reference | None = None
    evidence_reference: Reference | None = None
    confidence: float = 0.0
    expiry: str = ""
    validation_status: str = "pending"
    risk_if_incorrect: str = ""
    owner: str = ""
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()
    classification: str = "assumption"

    def __post_init__(self) -> None:
        if self.classification != "assumption":
            raise ValueError("assumptions must always be labeled")
        _scores(confidence=self.confidence)


CONSTRAINT_TYPES = frozenset(
    {
        "governance",
        "security",
        "runtime",
        "evidence",
        "knowledge",
        "confidence",
        "risk",
        "compatibility",
        "time_range",
        "source_count",
        "evidence_count",
        "result_size",
        "pause",
        "maintenance",
        "kill_switch",
    }
)


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    constraint_type: str
    description: str = ""
    limit: int | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    version: str = "1.0.0"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if self.constraint_type not in CONSTRAINT_TYPES:
            raise ValueError("unsupported reasoning constraint")
        if self.limit is not None and self.limit < 0:
            raise ValueError("constraint limit must be non-negative")
        object.__setattr__(self, "metadata", validate_safe_metadata(self.metadata))


@dataclass(frozen=True)
class ReasoningSession:
    reasoning_session_id: str
    profile_reference: Reference
    context_reference: Reference
    source_references: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    signal_references: tuple[Reference, ...] = ()
    observation_references: tuple[Reference, ...] = ()
    hypothesis_references: tuple[Reference, ...] = ()
    assumption_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    alternative_references: tuple[Reference, ...] = ()
    evaluation_references: tuple[Reference, ...] = ()
    confidence_reference: Reference | None = None
    recommendation_references: tuple[Reference, ...] = ()
    explanation_reference: Reference | None = None
    policy_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    trace_reference: Reference | None = None
    safe_summary: str = ""
    limitations: tuple[str, ...] = ()
    lifecycle: ReasoningLifecycle = ReasoningLifecycle.DRAFT
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "safe_metadata", validate_safe_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class Alternative:
    alternative_id: str
    reasoning_session_reference: Reference
    name: str
    description: str
    expected_outcome_reference: Reference | None = None
    evidence_references: tuple[Reference, ...] = ()
    knowledge_references: tuple[Reference, ...] = ()
    benefits: tuple[str, ...] = ()
    risks: tuple[str, ...] = ()
    constraints: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    evaluation_reference: Reference | None = None
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(confidence=self.confidence)


@dataclass(frozen=True)
class Comparison:
    comparison_id: str
    comparison_type: str
    left_reference: Reference
    right_reference: Reference
    summary: str
    supporting_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    causal_claim: bool = False
    version: str = "1.0.0"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if self.causal_claim:
            raise ValueError("unsupported causal conclusions are prohibited")


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    evaluation_type: str
    score: float
    factors: Mapping[str, float]
    weight_metadata: Mapping[str, float]
    supporting_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    explanation_summary: str = ""
    version: str = "1.0.0"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(score=self.score)
        _scores(**dict(self.factors))
        _scores(**dict(self.weight_metadata))
        object.__setattr__(self, "factors", immutable_metadata(self.factors))
        object.__setattr__(
            self, "weight_metadata", immutable_metadata(self.weight_metadata)
        )


@dataclass(frozen=True)
class Confidence:
    confidence_id: str
    original_confidence: float
    evidence_adjusted_confidence: float
    knowledge_adjusted_confidence: float
    source_adjusted_confidence: float
    freshness_adjusted_confidence: float
    risk_adjusted_confidence: float
    compatibility_adjusted_confidence: float
    governance_adjusted_confidence: float
    calibrated_confidence: float
    confidence_range_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    historical_accuracy_reference: Reference | None = None
    calibration_explanation: str = ""
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        for value in (
            self.original_confidence,
            self.evidence_adjusted_confidence,
            self.knowledge_adjusted_confidence,
            self.source_adjusted_confidence,
            self.freshness_adjusted_confidence,
            self.risk_adjusted_confidence,
            self.compatibility_adjusted_confidence,
            self.governance_adjusted_confidence,
            self.calibrated_confidence,
        ):
            _scores(confidence=value)
        object.__setattr__(
            self,
            "confidence_range_metadata",
            immutable_metadata(self.confidence_range_metadata),
        )


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    recommendation_type: str
    summary: str
    supporting_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        _scores(confidence=self.confidence)

    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Explanation:
    explanation_id: str
    reasoning_summary: str
    context_summary: str = ""
    evidence_used: tuple[Reference, ...] = ()
    evidence_missing: tuple[Reference, ...] = ()
    knowledge_used: tuple[Reference, ...] = ()
    sources_used: tuple[Reference, ...] = ()
    signals_considered: tuple[Reference, ...] = ()
    observations_considered: tuple[Reference, ...] = ()
    hypotheses_considered: tuple[Reference, ...] = ()
    assumptions: tuple[Reference, ...] = ()
    constraints: tuple[Reference, ...] = ()
    alternatives_considered: tuple[Reference, ...] = ()
    policies_applied: tuple[Reference, ...] = ()
    risks_considered: tuple[str, ...] = ()
    confidence_explanation: str = ""
    evaluation_breakdown: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    limitations: tuple[str, ...] = ()
    review_requirements: tuple[str, ...] = ()
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "evaluation_breakdown",
            validate_safe_metadata(self.evaluation_breakdown),
        )


@dataclass(frozen=True)
class Review:
    review_id: str
    review_type: str
    reviewer: str
    review_scope: str
    findings: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()
    advisory_recommendations: tuple[str, ...] = ()
    status: str = "pending"
    timestamp: str = ""
    audit_reference: Reference | None = None
    scope: ReasoningScope = ReasoningScope()


@dataclass(frozen=True)
class VersionMetadata:
    version: str
    effective_date: str = ""
    superseded_by: Reference | None = None
    change_reason: str = ""
    change_history: tuple[Reference, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )


ReasoningReference = Reference
ReasoningMeshProfile = Profile

__all__ = (
    "Alternative",
    "Assumption",
    "Comparison",
    "Confidence",
    "Constraint",
    "Context",
    "Evaluation",
    "Evidence",
    "Explanation",
    "FORBIDDEN_KEYS",
    "Hypothesis",
    "KnowledgeRecord",
    "Observation",
    "Profile",
    "ReasoningLifecycle",
    "ReasoningMeshProfile",
    "ReasoningReference",
    "ReasoningScope",
    "ReasoningSession",
    "Recommendation",
    "Reference",
    "Review",
    "Signal",
    "Source",
    "VersionMetadata",
    "immutable_metadata",
    "validate_safe_metadata",
)
