"""Domain contracts for bounded autonomous TikTok operations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MissionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    APPROVED = "approved"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MissionType(str, Enum):
    CONTENT = "content_operation"
    CAMPAIGN = "campaign_operation"
    GROWTH = "growth_operation"
    PUBLISHING = "publishing_operation"
    WORKFLOW = "workflow_operation"
    RESOURCE = "resource_operation"
    RUNTIME = "runtime_operation"
    RECOVERY = "recovery_operation"
    MIXED = "mixed_mission"


class ObjectiveType(str, Enum):
    PUBLISHING_STABILITY = "publishing_stability"
    RUNTIME_STABILITY = "runtime_stability"
    RESOURCE_UTILIZATION = "resource_utilization"
    WORKFLOW_SUCCESS = "workflow_success"
    RECOVERY_SUCCESS = "recovery_success"
    GROWTH_KPI = "growth_kpi"
    CAMPAIGN_KPI = "campaign_kpi"
    QUALITY_KPI = "quality_kpi"
    CUSTOM = "custom_bounded_objective"


class PolicyType(str, Enum):
    RISK = "risk_policy"
    APPROVAL = "approval_policy"
    SCHEDULING = "scheduling_policy"
    RECOVERY = "recovery_policy"
    RESOURCE = "resource_policy"
    EXECUTION = "execution_policy"
    COOLDOWN = "cooldown_policy"


class ConstraintType(str, Enum):
    RESOURCE_LIMITS = "resource_limits"
    RISK_THRESHOLDS = "risk_thresholds"
    APPROVAL_REQUIREMENTS = "approval_requirements"
    RUNTIME_HEALTH = "runtime_health"
    BROWSER_CAPACITY = "browser_capacity"
    DEVICE_CAPACITY = "device_capacity"
    QUEUE_CAPACITY = "queue_capacity"
    WORKSPACE_LIMITS = "workspace_limits"


class PlanningHorizon(str, Enum):
    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom_bounded_window"


@dataclass(frozen=True, slots=True)
class OperationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:autonomous:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in autonomous-operation data.")


@dataclass(slots=True)
class Objective:
    kind: ObjectiveType
    target: float
    unit: str
    description: str = ""

    def validate(self) -> None:
        if self.target < 0 or not self.unit:
            raise ValueError("Objectives require a bounded non-negative target.")
        if self.kind is ObjectiveType.CUSTOM and not self.description:
            raise ValueError("Custom objectives require a bounded description.")


@dataclass(slots=True)
class Policy:
    kind: PolicyType
    settings: dict[str, Any]

    def validate(self) -> None:
        validate_safe_mapping(self.settings)


@dataclass(slots=True)
class Constraint:
    kind: ConstraintType
    limit: float
    unit: str

    def validate(self) -> None:
        if self.limit < 0 or not self.unit:
            raise ValueError("Constraints require a non-negative limit and unit.")


@dataclass(slots=True)
class Mission:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    priority: int
    planning_horizon: PlanningHorizon
    owner: str
    mission_type: MissionType
    objectives: list[Objective]
    policies: list[Policy]
    constraints: list[Constraint]
    status: MissionStatus = MissionStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Mission identity and scope are required.")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be within [1, 5].")
        if not self.objectives:
            raise ValueError("At least one objective is required.")
        for objective in self.objectives:
            objective.validate()
        for policy in self.policies:
            policy.validate()
        for constraint in self.constraints:
            constraint.validate()
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MissionApproval:
    id: str
    mission_id: str
    tenant: str
    workspace: str
    reviewer: str
    approved: bool
    expires_at: datetime
    notes: str = ""


@dataclass(slots=True)
class MissionPlan:
    id: str
    mission_id: str
    tenant: str
    workspace: str
    task_references: list[str]
    checkpoint: str
    rollback_reference: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ExecutionState:
    mission_id: str
    tenant: str
    workspace: str
    delegated_references: dict[str, str]
    checkpoint: str
    progress: float = 0.0
    runtime_state: str = "pending"
    queue_state: str = "pending"
    risk_state: str = "clear"
    recovery_state: str = "idle"
    started_at: datetime = field(default_factory=utcnow)
    finished_at: datetime | None = None


@dataclass(slots=True)
class AuditEntry:
    mission_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    timestamp: datetime = field(default_factory=utcnow)
