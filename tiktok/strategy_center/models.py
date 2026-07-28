"""Bounded domain contracts for the TikTok Autonomous Strategy Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from math import isfinite
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class StrategyStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE_REFERENCE = "active_reference"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StrategyType(str, Enum):
    CONTENT = "content_strategy"
    CAMPAIGN = "campaign_strategy"
    PUBLISHING = "publishing_strategy"
    GROWTH = "growth_strategy"
    OPERATIONAL = "operational_strategy"
    RESOURCE = "resource_strategy"
    RUNTIME = "runtime_strategy"
    RECOVERY = "recovery_strategy"
    RISK_REDUCTION = "risk_reduction_strategy"
    MIXED = "mixed_strategy"
    CUSTOM_BOUNDED = "custom_bounded_strategy"


class ObjectiveType(str, Enum):
    PUBLISHING_RELIABILITY = "publishing_reliability"
    CONTENT_THROUGHPUT = "content_throughput"
    CAMPAIGN_COMPLETION = "campaign_completion"
    WORKFLOW_SUCCESS = "workflow_success"
    EXECUTION_SUCCESS = "execution_success"
    RECOVERY_SUCCESS = "recovery_success"
    RUNTIME_AVAILABILITY = "runtime_availability"
    RESOURCE_EFFICIENCY = "resource_efficiency"
    RISK_REDUCTION = "risk_reduction"
    GROWTH_KPI = "growth_kpi"
    BUSINESS_KPI = "business_kpi"
    CUSTOM_BOUNDED = "custom_bounded_objective"


class PlanningHorizon(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    CUSTOM_BOUNDED = "custom_bounded_window"


class OptionType(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    RELIABILITY_FOCUSED = "reliability_focused"
    PERFORMANCE_FOCUSED = "performance_focused"
    GROWTH_FOCUSED = "growth_focused"
    RESOURCE_EFFICIENT = "resource_efficient"
    RECOVERY_FOCUSED = "recovery_focused"
    RISK_REDUCTION = "risk_reduction"
    MANUAL_ASSISTED = "manual_assisted"


class ScenarioType(str, Enum):
    DRY_RUN = "dry_run"
    WHAT_IF = "what_if_analysis"
    CAPACITY = "capacity_scenario"
    SCHEDULE = "schedule_scenario"
    FAILURE = "failure_scenario"
    RECOVERY = "recovery_scenario"
    RISK = "risk_scenario"
    GROWTH = "growth_scenario"
    STRATEGY_COMPARISON = "strategy_comparison"


class ApprovalType(str, Enum):
    STRATEGY = "strategy_approval"
    HIGH_RISK = "high_risk_strategy_approval"
    RESOURCE = "resource_strategy_approval"
    RUNTIME = "runtime_strategy_approval"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class HandoffType(str, Enum):
    OPERATIONS_PLANNER = "operations_planner"
    DECISION_CENTER = "decision_center"
    OPTIMIZATION_CENTER = "optimization_center"
    AUTONOMOUS_OPERATION = "autonomous_operation"
    MISSION_ENGINE = "mission_engine"
    CAMPAIGN_CENTER = "campaign_center"
    CREATOR_WORKSPACE = "creator_workspace"
    CONTENT_PIPELINE = "content_pipeline"
    WORKFLOW_CENTER = "workflow_center"


class ReviewType(str, Enum):
    STRATEGY = "strategy_review"
    OUTCOME = "outcome_review"
    RISK = "risk_review"
    RESOURCE = "resource_review"
    MISSION = "mission_review"
    LESSONS_LEARNED = "lessons_learned"
    IMPROVEMENT = "improvement_recommendations"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class StrategyScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:strategy-center:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {
        "password",
        "secret",
        "token",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "session",
        "sessions",
        "proxy_password",
    }
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in strategy metadata.")
    for child in value.values():
        if isinstance(child, dict):
            validate_safe_mapping(child)


@dataclass(slots=True)
class StrategyObjective:
    kind: ObjectiveType
    target: float
    unit: str
    description: str = ""

    def validate(self) -> None:
        if not isfinite(self.target) or self.target < 0 or not self.unit.strip():
            raise ValueError(
                "Objectives require a finite non-negative target and unit."
            )
        if self.kind is ObjectiveType.CUSTOM_BOUNDED and not self.description.strip():
            raise ValueError("Custom objectives require a bounded description.")


@dataclass(slots=True)
class StrategyConstraint:
    name: str
    minimum: float
    maximum: float
    requested: float
    unit: str = "count"
    approval_required: bool = False

    def validate(self) -> None:
        values = (self.minimum, self.maximum, self.requested)
        if not all(isfinite(item) for item in values):
            raise ValueError("Constraint bounds must be finite.")
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("Constraint bounds must be non-negative and ordered.")
        if not self.minimum <= self.requested <= self.maximum:
            raise ValueError(f"{self.name} must remain within configured bounds.")
        if not self.name.strip() or not self.unit.strip():
            raise ValueError("Constraint name and unit are required.")


@dataclass(slots=True)
class Strategy:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    strategy_type: StrategyType
    planning_horizon: PlanningHorizon
    priority: int
    objectives: list[StrategyObjective]
    constraints: list[StrategyConstraint]
    status: StrategyStatus = StrategyStatus.DRAFT
    version: int = 1
    window_start: datetime | None = None
    window_end: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.description,
                self.tenant,
                self.workspace,
                self.owner,
            )
        ):
            raise ValueError(
                "Strategy identity, description, scope, and owner are required."
            )
        if not 1 <= self.priority <= 5:
            raise ValueError("Strategy priority must be within [1, 5].")
        if not self.objectives:
            raise ValueError("At least one bounded objective is required.")
        for objective in self.objectives:
            objective.validate()
        for constraint in self.constraints:
            constraint.validate()
        if self.planning_horizon is PlanningHorizon.CUSTOM_BOUNDED:
            if not self.window_start or not self.window_end:
                raise ValueError("Custom planning horizons require a bounded window.")
            if self.window_end <= self.window_start:
                raise ValueError("Planning window end must follow its start.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["strategy_type"] = self.strategy_type.value
        value["planning_horizon"] = self.planning_horizon.value
        return value


@dataclass(slots=True)
class StrategyContext:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    inputs: dict[str, dict[str, Any]]
    evidence_references: list[str]
    captured_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyOption:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    kind: OptionType
    schedule: list[str]
    resource_allocation: dict[str, float]
    mission_types: list[str]
    recovery_plan: list[str]
    expected_outcome: str
    bounded: bool = True


@dataclass(slots=True)
class StrategyEvaluation:
    id: str
    strategy_id: str
    option_id: str
    tenant: str
    workspace: str
    objective_score: float
    constraint_compliance: float
    risk_score: float
    capacity_score: float
    resource_score: float
    operational_feasibility: float
    historical_comparison: float
    confidence_score: float
    evidence_references: list[str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyScenario:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    kind: ScenarioType
    assumptions: dict[str, Any]
    result: dict[str, Any] = field(default_factory=dict)
    live_tiktok_access: bool = False
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyRecommendation:
    id: str
    strategy_id: str
    option_id: str
    tenant: str
    workspace: str
    recommended_objectives: list[str]
    recommended_schedule: list[str]
    recommended_resource_allocation: dict[str, float]
    recommended_mission_types: list[str]
    recommended_constraints: list[str]
    recommended_recovery_plan: list[str]
    expected_outcome: str
    risk_level: RiskLevel
    confidence: float
    evidence_references: list[str]
    advisory: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyApproval:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    kind: ApprovalType
    decision: ApprovalDecision
    reviewer: str
    notes: str
    expires_at: datetime
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyHandoff:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    target: HandoffType
    recommendation_reference: str
    approval_reference: str
    accepted_reference: str = ""
    reference_only: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyReview:
    id: str
    strategy_id: str
    tenant: str
    workspace: str
    reviewer: str
    kind: ReviewType
    summary: str
    lessons_learned: list[str] = field(default_factory=list)
    improvement_recommendations: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class StrategyHistory:
    strategy_id: str
    tenant: str
    workspace: str
    version: int
    status: StrategyStatus
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
