"""Validated domain contracts for TikTok workflow orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkflowStatus(str, Enum):
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


class NodeKind(str, Enum):
    ACCOUNT_CENTER = "account_center"
    BROWSER_RUNTIME = "browser_runtime"
    PROXY_CENTER = "proxy_center"
    ACCOUNT_FARMING = "ai_account_farming"
    CONTENT_CENTER = "content_center"
    PUBLISHING_CENTER = "publishing_center"
    DATA_COLLECTION_CENTER = "data_collection_center"
    INTERACTION_CENTER = "interaction_center"
    RISK_CONTROL_CENTER = "risk_control_center"
    MANUAL_APPROVAL = "manual_approval"
    DELAY = "delay"
    CONDITION = "condition"
    NOTIFICATION = "notification"


class ExecutionMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    ROLLED_BACK = "rolled_back"


class ScheduleKind(str, Enum):
    IMMEDIATE = "immediate"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CALENDAR = "calendar"


class ApprovalKind(str, Enum):
    WORKFLOW = "workflow"
    EXECUTION = "execution"
    HIGH_RISK_STEP = "high_risk_step"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ConditionKind(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    THRESHOLD = "threshold"
    HEALTH = "health"
    RISK_SCORE = "risk_score"
    TIME_WINDOW = "time_window"
    WORKSPACE_STATE = "workspace_state"
    ACCOUNT_STATE = "account_state"


@dataclass(frozen=True, slots=True)
class WorkflowScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:workflow:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_metadata(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets and session material must use encrypted references.")


@dataclass(slots=True)
class WorkflowNode:
    id: str
    kind: NodeKind
    name: str
    configuration: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 300
    maximum_retries: int = 0
    high_risk: bool = False

    def validate(self) -> None:
        if not self.id or not self.name:
            raise ValueError("Node ID and name are required.")
        if not 1 <= self.timeout_seconds <= 86_400:
            raise ValueError("Node timeout must be within [1, 86400] seconds.")
        if not 0 <= self.maximum_retries <= 10:
            raise ValueError("Maximum retries must be within [0, 10].")
        validate_metadata(self.configuration)


@dataclass(frozen=True, slots=True)
class WorkflowEdge:
    source: str
    target: str
    condition_reference: str = ""


@dataclass(slots=True)
class Workflow:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    version: int = 1
    status: WorkflowStatus = WorkflowStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    nodes: list[WorkflowNode] = field(default_factory=list)
    edges: list[WorkflowEdge] = field(default_factory=list)
    mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    maximum_runtime_seconds: int = 3600
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Workflow identity, workspace, and owner are required.")
        if self.version < 1:
            raise ValueError("Version must be positive.")
        if not 1 <= self.maximum_runtime_seconds <= 604_800:
            raise ValueError("Maximum runtime must be within [1, 604800] seconds.")
        validate_metadata(self.metadata)
        node_ids = {node.id for node in self.nodes}
        if len(node_ids) != len(self.nodes):
            raise ValueError("Workflow node IDs must be unique.")
        for node in self.nodes:
            node.validate()
        if any(
            edge.source not in node_ids or edge.target not in node_ids
            for edge in self.edges
        ):
            raise ValueError("Every edge must reference existing nodes.")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["mode"] = self.mode.value
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class WorkflowTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    description: str
    nodes: list[WorkflowNode]
    edges: list[WorkflowEdge] = field(default_factory=list)
    version: int = 1


@dataclass(slots=True)
class WorkflowVariable:
    name: str
    value: Any = None
    source: str = "workflow"
    encrypted_reference: str = ""
    required: bool = False

    def validate(self) -> None:
        if not self.name or self.source not in {"workflow", "environment", "runtime"}:
            raise ValueError("Variable name and valid source are required.")
        if self.required and self.value is None and not self.encrypted_reference:
            raise ValueError(f"Required variable is unresolved: {self.name}")
        if self.encrypted_reference and not self.encrypted_reference.startswith(
            "secret://"
        ):
            raise ValueError("Encrypted references must use the secret:// scheme.")


@dataclass(slots=True)
class WorkflowCondition:
    id: str
    kind: ConditionKind
    field: str = ""
    operator: str = "eq"
    expected: Any = True

    def evaluate(self, context: dict[str, Any]) -> bool:
        actual = context.get(self.field) if self.field else context.get(self.kind.value)
        operators = {
            "eq": lambda: actual == self.expected,
            "ne": lambda: actual != self.expected,
            "gt": lambda: actual is not None and actual > self.expected,
            "gte": lambda: actual is not None and actual >= self.expected,
            "lt": lambda: actual is not None and actual < self.expected,
            "lte": lambda: actual is not None and actual <= self.expected,
        }
        if self.operator not in operators:
            raise ValueError(f"Unsupported condition operator: {self.operator}")
        return operators[self.operator]()


@dataclass(slots=True)
class WorkflowSchedule:
    id: str
    tenant: str
    workspace: str
    workflow_reference: str
    kind: ScheduleKind
    timezone: str = "UTC"
    expression: str = ""
    execution_window: tuple[int, int] = (0, 24)
    maximum_concurrent_executions: int = 1
    enabled: bool = True

    def validate(self) -> None:
        start, end = self.execution_window
        if not self.id or not self.timezone or not 0 <= start < end <= 24:
            raise ValueError(
                "A valid schedule ID, timezone, and execution window are required."
            )
        if not 1 <= self.maximum_concurrent_executions <= 100:
            raise ValueError("Maximum concurrent executions must be within [1, 100].")


@dataclass(slots=True)
class Approval:
    id: str
    tenant: str
    workspace: str
    kind: ApprovalKind
    resource_reference: str
    reviewer: str
    expires_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    decided_by: str = ""
    decision_note: str = ""


@dataclass(slots=True)
class StepResult:
    node_reference: str
    status: ExecutionStatus
    attempt: int
    duration_seconds: float
    output: dict[str, Any] = field(default_factory=dict)
    error: str = ""


@dataclass(slots=True)
class WorkflowExecution:
    id: str
    tenant: str
    workspace: str
    workflow_reference: str
    workflow_version: int
    operator: str
    priority: int = 50
    status: ExecutionStatus = ExecutionStatus.QUEUED
    variables: list[WorkflowVariable] = field(default_factory=list)
    results: list[StepResult] = field(default_factory=list)
    checkpoint: int = 0
    retry_count: int = 0
    queue_time_seconds: float = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    cancellation_requested: bool = False

    def validate(self) -> None:
        if not self.id or not 0 <= self.priority <= 100:
            raise ValueError("Execution ID and priority within [0, 100] are required.")
        for variable in self.variables:
            variable.validate()


@dataclass(slots=True)
class HistoryEntry:
    execution_reference: str
    tenant: str
    workspace: str
    event: str
    state: str
    operator: str
    version: int
    occurred_at: datetime = field(default_factory=utcnow)
    detail: str = ""
