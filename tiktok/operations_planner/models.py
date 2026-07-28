"""Domain contracts for the Enterprise TikTok AI Operations Planner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlanStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    PAUSED = "paused"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class PlanningHorizon(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom_bounded_window"


class ObjectiveKind(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    CONTENT_PREPARATION = "content_preparation"
    PUBLISHING_RELIABILITY = "publishing_reliability"
    COLLECTION_RELIABILITY = "collection_reliability"
    INTERACTION_REVIEW = "interaction_review"
    WORKFLOW_COMPLETION = "workflow_completion"
    RISK_REDUCTION = "risk_reduction"
    RESOURCE_UTILIZATION = "resource_utilization"
    RUNTIME_STABILITY = "runtime_stability"
    BACKUP_READINESS = "backup_readiness"
    CUSTOM = "custom_bounded"


class StrategyKind(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    PERFORMANCE = "performance_focused"
    RELIABILITY = "reliability_focused"
    RISK_REDUCTION = "risk_reduction"
    RESOURCE_EFFICIENT = "resource_efficient"
    RECOVERY = "recovery_focused"
    MANUAL_ASSISTED = "manual_assisted"


class ApprovalKind(str, Enum):
    PLAN = "plan"
    HIGH_RISK_STEP = "high_risk_step"
    RESOURCE = "resource"
    SCHEDULE = "schedule"


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SimulationKind(str, Enum):
    DRY_RUN = "dry_run"
    WHAT_IF = "what_if"
    CAPACITY = "capacity"
    QUEUE = "queue"
    FAILURE = "failure"
    RECOVERY = "recovery"
    SCHEDULE_COMPARISON = "schedule_comparison"
    STRATEGY_COMPARISON = "strategy_comparison"


@dataclass(frozen=True, slots=True)
class PlannerScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:planner:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in planner metadata.")


@dataclass(slots=True)
class Bound:
    name: str
    minimum: float
    maximum: float
    requested: float
    unit: str = "count"

    def validate(self) -> None:
        if self.minimum < 0 or self.maximum < self.minimum:
            raise ValueError("Constraint bounds must be finite and ordered.")
        if not self.minimum <= self.requested <= self.maximum:
            raise ValueError(f"{self.name} must remain within configured bounds.")


@dataclass(slots=True)
class Objective:
    kind: ObjectiveKind
    target: float
    unit: str
    description: str = ""

    def validate(self) -> None:
        if self.target < 0 or not self.unit:
            raise ValueError(
                "Objectives require a non-negative bounded target and unit."
            )
        if self.kind is ObjectiveKind.CUSTOM and not self.description:
            raise ValueError("Custom objectives require a bounded description.")


@dataclass(slots=True)
class OperationsPlan:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    planning_horizon: PlanningHorizon
    priority: int
    objectives: list[Objective]
    strategy: StrategyKind = StrategyKind.CONSERVATIVE
    constraints: list[Bound] = field(default_factory=list)
    status: PlanStatus = PlanStatus.DRAFT
    version: int = 1
    window_start: datetime | None = None
    window_end: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Plan identity and scope are required.")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be within [1, 5].")
        if not self.objectives:
            raise ValueError("At least one objective is required.")
        for objective in self.objectives:
            objective.validate()
        for constraint in self.constraints:
            constraint.validate()
        if self.planning_horizon is PlanningHorizon.CUSTOM:
            if not self.window_start or not self.window_end:
                raise ValueError("Custom horizons require a bounded window.")
            if self.window_end <= self.window_start:
                raise ValueError("Planning window end must follow its start.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["planning_horizon"] = self.planning_horizon.value
        value["strategy"] = self.strategy.value
        return value


@dataclass(slots=True)
class PlanningSnapshot:
    plan_id: str
    tenant: str
    workspace: str
    inputs: dict[str, dict[str, Any]]
    captured_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Recommendation:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    actions: list[str]
    schedule: list[str]
    resource_allocation: dict[str, float]
    concurrency: int
    cooldown_seconds: int
    pauses: list[str]
    recovery: list[str]
    expected_outcome: str
    risk_level: RiskLevel
    confidence: float
    evidence_references: list[str]
    advisory: bool = True


@dataclass(slots=True)
class Simulation:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    kind: SimulationKind
    assumptions: dict[str, Any]
    result: dict[str, Any]
    live_access: bool = False
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Approval:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    kind: ApprovalKind
    decision: ApprovalDecision
    reviewer: str
    notes: str
    expires_at: datetime
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ExecutionHandoff:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    automation_plan_reference: str
    workflow_reference: str
    scheduled_task_references: list[str]
    resource_reservations: list[str]
    execution_window: str
    checkpoints: list[str]
    rollback_plan: str
    accepted_references: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class PlanReview:
    id: str
    plan_id: str
    tenant: str
    workspace: str
    reviewer: str
    execution_review: str
    outcome_review: str
    risk_review: str
    resource_review: str
    lessons_learned: list[str]
    improvement_recommendations: list[str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class HistoryEntry:
    plan_id: str
    tenant: str
    workspace: str
    version: int
    status: PlanStatus
    actor: str
    detail: str
    timestamp: datetime = field(default_factory=utcnow)
