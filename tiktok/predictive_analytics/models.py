"""Domain models for the advisory TikTok Predictive Analytics Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "credential", "api_key"}
)
MAX_METADATA_SIZE = 32_768
MAX_REFERENCES = 100


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_ratio(value: float, name: str) -> None:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be within [0, 1].")


def validate_references(references: tuple[str, ...]) -> None:
    if not references or len(references) > MAX_REFERENCES:
        raise ValueError("One to 100 evidence references are required.")
    if any("://" not in reference for reference in references):
        raise ValueError("Evidence must use opaque reference URIs.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in predictive analytics records.")
    if len(str(value)) > MAX_METADATA_SIZE:
        raise ValueError("Metadata exceeds the bounded size.")


@dataclass(frozen=True, slots=True)
class PredictiveContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:predictive:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(frozen=True, slots=True)
class PredictiveProfile:
    id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    sources: tuple[str, ...]
    horizon_days: int
    history_start: datetime
    history_end: datetime
    target_metric: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self, *, max_history_days: int, max_horizon_days: int) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.tenant,
                self.workspace,
                self.owner,
                self.target_metric,
            )
        ):
            raise ValueError("Profile identity, ownership, and target are required.")
        if not self.sources:
            raise ValueError("At least one approved source is required.")
        if self.history_start >= self.history_end:
            raise ValueError("History start must precede its end.")
        if (self.history_end - self.history_start).days > max_history_days:
            raise ValueError("Historical range exceeds the configured bound.")
        if not 1 <= self.horizon_days <= max_horizon_days:
            raise ValueError("Forecast horizon exceeds the configured bound.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class TrendAnalysis:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    metric: str
    direction: str
    slope: float
    observations: int
    window_days: int
    evidence_references: tuple[str, ...]
    explanation: str
    causal_claim: bool = False


@dataclass(frozen=True, slots=True)
class Forecast:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    metric: str
    horizon_days: int
    predicted_value: float
    lower_bound: float
    upper_bound: float
    confidence: float
    method: str
    generated_at: datetime
    evidence_references: tuple[str, ...]
    assumptions: tuple[str, ...]
    advisory_only: bool = True
    direct_execution: bool = False


@dataclass(frozen=True, slots=True)
class Scenario:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    name: str
    assumptions: tuple[str, ...]
    projected_value: float
    delta_from_baseline: float
    risk_score: float
    confidence: float
    explanation: str


@dataclass(frozen=True, slots=True)
class CapacityForecast:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    resource: str
    horizon_days: int
    required_capacity: float
    available_capacity: float
    gap: float
    confidence: float
    evidence_references: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RiskForecast:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    risk_type: str
    horizon_days: int
    current_score: float
    predicted_score: float
    trend: str
    confidence: float
    evidence_references: tuple[str, ...]
    mitigation_reference: str | None = None


@dataclass(frozen=True, slots=True)
class ConfidenceEstimate:
    id: str
    forecast_id: str
    tenant: str
    workspace: str
    score: float
    sample_size: int
    data_quality: float
    stability: float
    calibration_error: float
    explanation: str


@dataclass(frozen=True, slots=True)
class PredictiveRecommendation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    category: str
    summary: str
    rationale: str
    evidence_references: tuple[str, ...]
    confidence: float
    advisory_only: bool = True
    automatic_decision: bool = False
    direct_execution: bool = False
    runtime_change: bool = False
    publishing: bool = False


@dataclass(frozen=True, slots=True)
class ForecastEvaluation:
    id: str
    forecast_id: str
    tenant: str
    workspace: str
    actual_value_reference: str
    actual_value: float
    absolute_error: float
    percentage_error: float
    within_confidence_range: bool
    evaluated_at: datetime
