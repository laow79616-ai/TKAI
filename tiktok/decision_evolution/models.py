"""Domain models for advisory TikTok decision-quality evolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "cookie",
        "session",
        "credential",
        "proxy",
        "api_key",
    }
)
MAX_METADATA_SIZE = 32_768
MAX_REFERENCES = 100


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    keys = {key.casefold() for key in value}
    if SECRET_KEYS & keys:
        raise ValueError("Secrets are forbidden in decision-evolution records.")
    if len(str(value)) > MAX_METADATA_SIZE:
        raise ValueError("Metadata exceeds the bounded size.")


def validate_ratio(value: float, field_name: str = "Value") -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{field_name} must be within [0, 1].")


def validate_references(references: tuple[str, ...]) -> None:
    if len(references) > MAX_REFERENCES:
        raise ValueError("Evidence references exceed the bounded result size.")
    if any(not reference or "://" not in reference for reference in references):
        raise ValueError("References must be non-empty opaque reference URIs.")


class ProfileStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    ANALYZING = "analyzing"
    READY = "ready"
    REVIEW = "review"
    APPROVED_REFERENCE = "approved_reference"
    ARCHIVED = "archived"
    DELETED = "deleted"


ALLOWED_TRANSITIONS: dict[ProfileStatus, frozenset[ProfileStatus]] = {
    ProfileStatus.DRAFT: frozenset(
        {ProfileStatus.COLLECTING, ProfileStatus.ARCHIVED, ProfileStatus.DELETED}
    ),
    ProfileStatus.COLLECTING: frozenset(
        {ProfileStatus.ANALYZING, ProfileStatus.ARCHIVED}
    ),
    ProfileStatus.ANALYZING: frozenset(
        {ProfileStatus.READY, ProfileStatus.COLLECTING, ProfileStatus.ARCHIVED}
    ),
    ProfileStatus.READY: frozenset(
        {ProfileStatus.REVIEW, ProfileStatus.ANALYZING, ProfileStatus.ARCHIVED}
    ),
    ProfileStatus.REVIEW: frozenset(
        {
            ProfileStatus.APPROVED_REFERENCE,
            ProfileStatus.ANALYZING,
            ProfileStatus.ARCHIVED,
        }
    ),
    ProfileStatus.APPROVED_REFERENCE: frozenset({ProfileStatus.ARCHIVED}),
    ProfileStatus.ARCHIVED: frozenset({ProfileStatus.DELETED}),
    ProfileStatus.DELETED: frozenset(),
}


@dataclass(frozen=True, slots=True)
class DecisionEvolutionContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:decision-evolution:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class DecisionEvolutionProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    scope: tuple[str, ...]
    time_range_start: datetime
    time_range_end: datetime
    status: ProfileStatus = ProfileStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self, *, max_range_days: int) -> None:
        identity = (
            self.id,
            self.name,
            self.description,
            self.tenant,
            self.workspace,
            self.owner,
        )
        if not all(identity):
            raise ValueError(
                "Profile identity, description, and ownership are required."
            )
        if not self.scope:
            raise ValueError("At least one bounded source is required.")
        if self.time_range_start >= self.time_range_end:
            raise ValueError("Time range start must precede its end.")
        if (self.time_range_end - self.time_range_start).days > max_range_days:
            raise ValueError("Time range exceeds the configured bound.")
        if self.version < 1:
            raise ValueError("Profile version must be positive.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    decision_reference: str
    decision_type: str
    context_reference: str
    recommendation_reference: str | None
    approval_reference: str | None
    evidence_references: tuple[str, ...]
    confidence: float
    risk_level: str
    status: str
    timestamp: datetime
    version: int = 1


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    expected_outcome: str
    observed_outcome_reference: str
    success_criteria: tuple[str, ...]
    outcome_status: str
    deviation: float
    latency_seconds: float
    resource_impact_reference: str | None
    risk_impact_reference: str | None
    recovery_impact_reference: str | None
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DecisionBaseline:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    historical_decision_quality: float
    historical_approval_time: float
    historical_success_rate: float
    historical_failure_rate: float
    historical_recovery_rate: float
    historical_confidence: float
    historical_risk: float
    previous_period: str
    rolling_window_days: int
    version: int = 1


@dataclass(frozen=True, slots=True)
class DecisionPattern:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    pattern_type: str
    description: str
    evidence_references: tuple[str, ...]
    support_count: int
    causal_claim: bool = False


@dataclass(frozen=True, slots=True)
class DecisionComparison:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    comparison_type: str
    expected_value: float
    observed_value: float
    difference: float
    explanation: str


@dataclass(frozen=True, slots=True)
class ScoreComponent:
    name: str
    score: float
    weight: float
    explanation: str


@dataclass(frozen=True, slots=True)
class DecisionEvaluation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    decision_quality_score: float
    evidence_completeness: float
    constraint_compliance: float
    risk_calibration: float
    confidence_calibration: float
    outcome_accuracy: float
    resource_estimate_accuracy: float
    schedule_accuracy: float
    recovery_appropriateness: float
    approval_efficiency: float
    score_breakdown: tuple[ScoreComponent, ...]
    version: int = 1


@dataclass(frozen=True, slots=True)
class ConfidenceAnalysis:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    original_confidence: float
    observed_accuracy_reference: str
    observed_accuracy: float
    calibration_difference: float
    confidence_trend: str
    confidence_distribution: tuple[float, ...]
    explanation: str


@dataclass(frozen=True, slots=True)
class DecisionLesson:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    what_worked: tuple[str, ...]
    what_failed: tuple[str, ...]
    evidence_used: tuple[str, ...]
    evidence_missing: tuple[str, ...]
    constraints_missed: tuple[str, ...]
    risk_factors_missed: tuple[str, ...]
    resource_factors_missed: tuple[str, ...]
    schedule_factors_missed: tuple[str, ...]
    recovery_factors: tuple[str, ...]
    improvement_summary: str
    version: int = 1


@dataclass(frozen=True, slots=True)
class EvolutionRecommendation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    recommendation_type: str
    summary: str
    rationale: str
    evidence_references: tuple[str, ...]
    knowledge_evolution_handoff_reference: str | None = None
    learning_center_handoff_reference: str | None = None
    governance_review_reference: str | None = None
    advisory_only: bool = True
    automatic_approval: bool = False
    direct_execution: bool = False
    version: int = 1


@dataclass(frozen=True, slots=True)
class DecisionReview:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    review_type: str
    reviewer: str
    findings: tuple[str, ...]
    recommendations: tuple[str, ...]
    status: str
    audit_reference: str


@dataclass(frozen=True, slots=True)
class VersionRecord:
    id: str
    resource_type: str
    resource_id: str
    tenant: str
    workspace: str
    version: int
    effective_date: datetime
    superseded_by: str | None
    change_history: tuple[str, ...]
