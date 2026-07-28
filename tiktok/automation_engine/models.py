"""Domain contracts for bounded TikTok automation."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AutomationStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    READY = "ready"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TriggerKind(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT = "event_triggered"
    HEALTH = "health_triggered"
    RECOVERY = "recovery_triggered"
    WORKFLOW = "workflow_triggered"
    CUSTOM = "custom"


class ConditionKind(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    BROWSER_HEALTH = "browser_health"
    DEVICE_HEALTH = "device_health"
    PROXY_HEALTH = "proxy_health"
    RISK_SCORE = "risk_score"
    WORKFLOW_STATE = "workflow_state"
    RUNTIME_STATE = "runtime_state"
    TIME_WINDOW = "time_window"
    APPROVAL = "approval"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    TIMED_OUT = "timed_out"
    ROLLED_BACK = "rolled_back"
    BLOCKED = "blocked"


class QueueKind(str, Enum):
    EXECUTION = "execution"
    PRIORITY = "priority"
    RETRY = "retry"
    RECOVERY = "recovery"
    DELAYED = "delayed"


@dataclass(frozen=True, slots=True)
class AutomationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:automation:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_metadata(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets must be stored as encrypted references.")


@dataclass(slots=True)
class Automation:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    version: int = 1
    status: AutomationStatus = AutomationStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    plan_reference: str = ""
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Automation identity, workspace, and owner are required.")
        if self.version < 1:
            raise ValueError("Version must be positive.")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class AutomationPlan:
    id: str
    tenant: str
    workspace: str
    name: str
    workflow_reference: str
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    maximum_executions: int = 1
    maximum_concurrency: int = 1
    timeout_seconds: int = 3600
    maximum_attempts: int = 3
    backoff_seconds: int = 30
    cooldown_seconds: int = 60
    approval_required: bool = True
    risk_policy_reference: str = ""
    schedule_reference: str = ""
    reusable: bool = True

    def validate(self) -> None:
        if not all((self.id, self.tenant, self.workspace, self.name)):
            raise ValueError("Plan identity and scope are required.")
        if not (
            1 <= self.maximum_executions <= 10_000
            and 1 <= self.maximum_concurrency <= 100
            and 1 <= self.timeout_seconds <= 604_800
            and 1 <= self.maximum_attempts <= 10
            and 0 <= self.backoff_seconds <= 86_400
            and 0 <= self.cooldown_seconds <= 86_400
        ):
            raise ValueError("Plan execution, retry, and timing limits are invalid.")


@dataclass(slots=True)
class AutomationTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    plan_reference: str
    version: int = 1


@dataclass(slots=True)
class AutomationTrigger:
    id: str
    tenant: str
    workspace: str
    automation_reference: str
    kind: TriggerKind
    configuration: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    def validate(self) -> None:
        validate_metadata(self.configuration)
        if self.kind is TriggerKind.CUSTOM and not str(
            self.configuration.get("interface", "")
        ).startswith("automation-trigger://"):
            raise ValueError("Custom triggers require a bounded trigger interface.")


@dataclass(slots=True)
class AutomationCondition:
    id: str
    tenant: str
    workspace: str
    kind: ConditionKind
    field: str
    operator: str = "eq"
    expected: Any = True

    def evaluate(self, context: dict[str, Any]) -> bool:
        actual = context.get(self.field)
        operators = {
            "eq": lambda: actual == self.expected,
            "ne": lambda: actual != self.expected,
            "gt": lambda: actual is not None and actual > self.expected,
            "gte": lambda: actual is not None and actual >= self.expected,
            "lt": lambda: actual is not None and actual < self.expected,
            "lte": lambda: actual is not None and actual <= self.expected,
            "in": lambda: actual in self.expected,
        }
        if self.operator not in operators:
            raise ValueError(f"Unsupported condition operator: {self.operator}")
        return bool(operators[self.operator]())


@dataclass(slots=True)
class AutomationApproval:
    id: str
    tenant: str
    workspace: str
    automation_reference: str
    reviewer: str
    approved: bool = False
    decided_by: str = ""


APPROVED_MODULES = frozenset(
    {
        "runtime_manager",
        "resource_center",
        "task_scheduler",
        "browser_cluster",
        "device_center",
        "account_center",
        "browser_runtime",
        "proxy_center",
        "workflow_center",
        "operations_center",
        "risk_control",
        "publishing_center",
        "data_collection",
        "interaction_center",
        "analytics_center",
        "local_runtime",
    }
)


@dataclass(slots=True)
class ExecutionStep:
    id: str
    module: str
    action: str
    condition_reference: str = ""
    checkpoint: bool = True
    rollback_action: str = ""
    configuration: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        validate_metadata(self.configuration)
        if self.module not in APPROVED_MODULES:
            raise ValueError(f"Unsupported TikTok module: {self.module}")


@dataclass(slots=True)
class AutomationExecution:
    id: str
    tenant: str
    workspace: str
    automation_reference: str
    plan_reference: str
    operator: str
    steps: list[ExecutionStep] = field(default_factory=list)
    priority: int = 50
    status: ExecutionStatus = ExecutionStatus.QUEUED
    checkpoint: int = 0
    retry_count: int = 0
    recovery_count: int = 0
    last_error: str = ""
    restriction_unresolved: bool = False
    graceful_stop_requested: bool = False
    started_at: datetime | None = None
    finished_at: datetime | None = None
    delayed_until: datetime | None = None

    def validate(self) -> None:
        if not self.id or not 0 <= self.priority <= 100:
            raise ValueError("Execution ID and priority within [0, 100] are required.")
        for step in self.steps:
            step.validate()


@dataclass(slots=True)
class AuditEvent:
    resource_reference: str
    tenant: str
    workspace: str
    event: str
    state: str
    actor: str
    detail: str = ""
    occurred_at: datetime = field(default_factory=utcnow)
