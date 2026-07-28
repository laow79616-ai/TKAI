"""Bounded domain contracts for the enterprise TikTok AI Task Scheduler."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, IntEnum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TaskStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    READY = "ready"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    ALLOCATED = "allocated"
    RUNNING = "running"
    PAUSED = "paused"
    RETRYING = "retrying"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TaskType(str, Enum):
    ACCOUNT_HEALTH_CHECK = "account_health_check"
    BROWSER_LAUNCH = "browser_launch"
    BROWSER_RECOVERY = "browser_recovery"
    DEVICE_ALLOCATION = "device_allocation"
    DEVICE_RECOVERY = "device_recovery"
    PROXY_HEALTH_CHECK = "proxy_health_check"
    PROXY_ALLOCATION = "proxy_allocation"
    WORKFLOW_EXECUTION = "workflow_execution"
    PUBLISHING_JOB = "publishing_job"
    COLLECTION_JOB = "collection_job"
    INTERACTION_TASK = "interaction_task"
    RISK_EVALUATION = "risk_evaluation"
    ANALYTICS_AGGREGATION = "analytics_aggregation"
    BACKUP = "backup"
    DIAGNOSTICS = "diagnostics"
    CUSTOM_BOUNDED = "custom_bounded"


class Priority(IntEnum):
    BACKGROUND = 10
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


class ScheduleKind(str, Enum):
    IMMEDIATE = "immediate"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    INTERVAL = "interval"
    CALENDAR_WINDOW = "calendar_window"
    EVENT_TRIGGERED = "event_triggered"
    DEPENDENCY_TRIGGERED = "dependency_triggered"


class MissedRunPolicy(str, Enum):
    SKIP = "skip"
    RUN_ONCE = "run_once"
    RESCHEDULE = "reschedule"


class DependencyRequirement(str, Enum):
    SUCCESS = "required_success"
    COMPLETION = "required_completion"
    OPTIONAL = "optional"


class WorkerStatus(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    DRAINING = "draining"
    OFFLINE = "offline"
    UNHEALTHY = "unhealthy"


class FailureCategory(str, Enum):
    VALIDATION = "validation"
    APPROVAL = "approval"
    RISK = "risk"
    RESOURCE = "resource"
    ACCOUNT = "account"
    BROWSER = "browser"
    DEVICE = "device"
    PROXY = "proxy"
    WORKFLOW = "workflow"
    PUBLISHING = "publishing"
    COLLECTION = "collection"
    INTERACTION = "interaction"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class SchedulerScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:scheduler:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


SECRET_KEYS = {
    "password",
    "secret",
    "token",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "session",
    "proxy_password",
    "api_key",
}


def validate_safe_payload(value: dict[str, Any], maximum_bytes: int) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).casefold() in SECRET_KEYS:
                    raise ValueError(
                        "Secrets, cookies, sessions, and credentials are forbidden."
                    )
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise TypeError("Payload values must be JSON-safe.")

    walk(value)
    if len(json.dumps(value, default=str).encode()) > maximum_bytes:
        raise ValueError("Task payload exceeds the configured bounded size.")


@dataclass(slots=True)
class Schedule:
    kind: ScheduleKind = ScheduleKind.IMMEDIATE
    timezone: str = "UTC"
    start_time: datetime | None = None
    end_time: datetime | None = None
    interval_seconds: int | None = None
    maximum_runs: int = 1
    runs: int = 0
    missed_run_policy: MissedRunPolicy = MissedRunPolicy.SKIP
    event_reference: str = ""

    def validate(self) -> None:
        if not 1 <= self.maximum_runs <= 10000:
            raise ValueError("Maximum runs must be within [1, 10000].")
        if self.end_time and self.start_time and self.end_time <= self.start_time:
            raise ValueError("Schedule end time must follow start time.")
        if self.kind is ScheduleKind.INTERVAL and not (
            self.interval_seconds and 1 <= self.interval_seconds <= 31_536_000
        ):
            raise ValueError("Interval schedules require a bounded interval.")


@dataclass(slots=True)
class RetryPolicy:
    maximum_attempts: int = 3
    retry_delay_seconds: int = 5
    exponential_backoff: bool = True
    cooldown_seconds: int = 0
    eligible_categories: frozenset[FailureCategory] = frozenset(
        {
            FailureCategory.RESOURCE,
            FailureCategory.BROWSER,
            FailureCategory.DEVICE,
            FailureCategory.PROXY,
            FailureCategory.WORKFLOW,
            FailureCategory.TIMEOUT,
            FailureCategory.UNKNOWN,
        }
    )

    def validate(self, global_maximum: int) -> None:
        if not 0 <= self.maximum_attempts <= global_maximum:
            raise ValueError("Retry attempts exceed the configured bounded limit.")
        if not 0 <= self.retry_delay_seconds <= 86400:
            raise ValueError("Retry delay must be within [0, 86400].")

    def delay_for(self, attempt: int) -> int:
        multiplier = 2 ** max(0, attempt - 1) if self.exponential_backoff else 1
        return min(86400, self.retry_delay_seconds * multiplier + self.cooldown_seconds)


@dataclass(slots=True)
class ScheduledTask:
    id: str
    name: str
    description: str
    task_type: TaskType
    tenant: str
    workspace: str
    owner: str
    account_reference: str = ""
    browser_reference: str = ""
    device_reference: str = ""
    proxy_reference: str = ""
    workflow_reference: str = ""
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    schedule: Schedule = field(default_factory=Schedule)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    approval_reference: str = ""
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self, limits: SchedulerLimits) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Task identity, scope, and owner are required.")
        if not 1 <= int(self.priority) <= 100:
            raise ValueError("Priority must be within [1, 100].")
        self.schedule.validate()
        self.retry_policy.validate(limits.maximum_retry_attempts)
        validate_safe_payload(self.metadata, limits.maximum_payload_size)
        validate_safe_payload(self.payload, limits.maximum_payload_size)
        if (
            self.task_type is TaskType.CUSTOM_BOUNDED
            and "handler_reference" not in self.payload
        ):
            raise ValueError("Custom tasks require a registered handler_reference.")
        forbidden = {"code", "command", "script", "shell", "executable"}
        if forbidden & {str(key).casefold() for key in self.payload}:
            raise ValueError("Arbitrary code execution fields are forbidden.")


@dataclass(slots=True)
class TaskDependency:
    task_id: str
    depends_on: str
    requirement: DependencyRequirement = DependencyRequirement.SUCCESS
    parallel: bool = False
    timeout_seconds: int = 3600


@dataclass(slots=True)
class Worker:
    id: str
    worker_type: str
    capacity: int
    supported_task_types: frozenset[TaskType]
    workspace_scope: str = "*"
    current_load: int = 0
    status: WorkerStatus = WorkerStatus.IDLE
    heartbeat: datetime = field(default_factory=utcnow)
    health: str = "healthy"
    last_active: datetime = field(default_factory=utcnow)

    @property
    def available(self) -> bool:
        return (
            self.status in {WorkerStatus.IDLE, WorkerStatus.ACTIVE}
            and self.health == "healthy"
            and self.current_load < self.capacity
        )


@dataclass(slots=True)
class Allocation:
    id: str
    task_id: str
    tenant: str
    workspace: str
    worker_id: str
    resources: dict[str, str]
    expires_at: datetime
    released: bool = False


@dataclass(slots=True)
class Execution:
    id: str
    task_id: str
    tenant: str
    workspace: str
    worker_id: str
    status: TaskStatus = TaskStatus.ALLOCATED
    attempt: int = 1
    progress: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    outcome: dict[str, Any] = field(default_factory=dict)
    cancellation_requested: bool = False


@dataclass(slots=True)
class Checkpoint:
    id: str
    execution_id: str
    tenant: str
    workspace: str
    execution_state: dict[str, Any]
    completed_steps: list[str]
    pending_steps: list[str]
    resource_references: dict[str, str]
    retry_position: int
    expires_at: datetime
    integrity: str


@dataclass(slots=True)
class Failure:
    id: str
    task_id: str
    execution_id: str
    tenant: str
    workspace: str
    category: FailureCategory
    detail: str
    retry_eligible: bool
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class SchedulerLimits:
    maximum_global_tasks: int = 10000
    maximum_workspace_tasks: int = 1000
    maximum_account_tasks: int = 100
    maximum_browser_tasks: int = 100
    maximum_device_tasks: int = 100
    maximum_proxy_tasks: int = 100
    maximum_concurrent_executions: int = 32
    maximum_queue_depth: int = 5000
    maximum_retry_attempts: int = 8
    maximum_runtime_seconds: int = 3600
    maximum_payload_size: int = 65536
    maximum_dependency_depth: int = 32
    reservation_timeout_seconds: int = 300
    maximum_recovery_attempts: int = 3

    def validate(self) -> None:
        values = asdict(self)
        if any(not isinstance(value, int) or value <= 0 for value in values.values()):
            raise ValueError("All scheduler limits must be positive bounded integers.")
        if self.maximum_retry_attempts > 100 or self.maximum_dependency_depth > 100:
            raise ValueError("Retry attempts and dependency depth may not exceed 100.")
        if self.maximum_payload_size > 1_048_576:
            raise ValueError("Maximum payload size may not exceed 1 MiB.")

    def reservation_expiry(self) -> datetime:
        return utcnow() + timedelta(seconds=self.reservation_timeout_seconds)
