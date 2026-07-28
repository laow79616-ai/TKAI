"""Domain contracts for the Enterprise TikTok AI Growth Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GrowthStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    PROPOSED = "proposed"
    REVIEW = "review"
    APPROVED = "approved"
    TRACKING = "tracking"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class GrowthObjective(str, Enum):
    FOLLOWER_GROWTH = "follower_growth"
    CONTENT_OUTPUT = "content_output"
    PUBLISHING_CONSISTENCY = "publishing_consistency"
    CONTENT_QUALITY = "content_quality"
    ENGAGEMENT_TREND_REFERENCE = "engagement_trend_reference"
    RETENTION_TREND_REFERENCE = "retention_trend_reference"
    ACCOUNT_HEALTH = "account_health"
    CUSTOM_BOUNDED = "custom_bounded_goal"


class KPIKind(str, Enum):
    PUBLISHING_FREQUENCY = "publishing_frequency"
    REVIEW_THROUGHPUT = "review_throughput"
    APPROVAL_TIME = "approval_time"
    PIPELINE_THROUGHPUT = "pipeline_throughput"
    WORKFLOW_SUCCESS = "workflow_success"
    RECOVERY_SUCCESS = "recovery_success"
    RUNTIME_AVAILABILITY = "runtime_availability"
    RESOURCE_UTILIZATION = "resource_utilization"
    TREND_SCORE = "trend_score"


class TrendPeriod(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    HISTORICAL_COMPARISON = "historical_comparison"
    FORECAST_REFERENCE = "forecast_reference"


class RecommendationKind(str, Enum):
    GROWTH_OPPORTUNITIES = "growth_opportunities"
    PUBLISHING_CADENCE = "publishing_cadence"
    RESOURCE_ALLOCATION = "resource_allocation"
    CONTENT_PLANNING = "content_planning"
    CAMPAIGN_PLANNING = "campaign_planning"
    WORKFLOW_OPTIMIZATION = "workflow_optimization"
    RUNTIME_OPTIMIZATION = "runtime_optimization"
    RISK_REDUCTION = "risk_reduction"


class SimulationKind(str, Enum):
    FORECAST = "forecast"
    CAPACITY = "capacity"
    TREND = "trend"
    SCHEDULE = "schedule"
    GROWTH_PROJECTION = "growth_projection"


@dataclass(frozen=True, slots=True)
class RequestScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:growth:read"})


def validate_metadata(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in growth metadata.")


def validate_reference(reference: str) -> None:
    if not reference.startswith(("ref://", "encrypted://")):
        raise ValueError("Inputs must use opaque or encrypted read-only references.")


@dataclass(slots=True)
class GrowthProfile:
    id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    growth_objective: GrowthObjective
    priority: int = 50
    status: GrowthStatus = GrowthStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity and isolation scope are required.")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be within [1, 100].")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["growth_objective"] = self.growth_objective.value
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class GrowthGoal:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: GrowthObjective
    baseline: float
    target: float
    unit: str
    bounded_definition: str = ""


@dataclass(slots=True)
class KPIRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: KPIKind
    value: float
    unit: str
    source_reference: str
    observed_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class TrendRecord:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    period: TrendPeriod
    score: float
    change: float
    source_references: list[str]
    summary: str


@dataclass(slots=True)
class GrowthRecommendation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: RecommendationKind
    title: str
    rationale: str
    expected_effect: str
    evidence_references: list[str]
    confidence: float
    proposal_reference: str = ""
    approved: bool = False


@dataclass(slots=True)
class GrowthOpportunity:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    title: str
    impact_score: float
    effort_score: float
    evidence_references: list[str]


@dataclass(slots=True)
class GrowthSimulation:
    id: str
    profile_id: str
    tenant: str
    workspace: str
    kind: SimulationKind
    assumptions: dict[str, float]
    projected_value: float
    confidence: float
    result_reference: str
    live_dependency: bool = False


@dataclass(slots=True)
class Approval:
    id: str
    recommendation_id: str
    tenant: str
    workspace: str
    reviewer: str
    approved: bool
    notes: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditEvent:
    profile_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
