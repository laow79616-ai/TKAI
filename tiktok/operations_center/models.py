"""Domain contracts for the enterprise TikTok Operations Command Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OperationsStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    PAUSED = "paused"
    RECOVERING = "recovering"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TaskStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class IncidentStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    MITIGATING = "mitigating"
    RESOLVED = "resolved"
    CLOSED = "closed"


class ActionKind(str, Enum):
    PAUSE_ACCOUNT = "pause_account"
    RESUME_ACCOUNT = "resume_account"
    STOP_BROWSER = "stop_browser"
    RECOVER_BROWSER = "recover_browser"
    RELEASE_PROXY = "release_proxy"
    ROTATE_PROXY_REFERENCE = "rotate_proxy_reference"
    PAUSE_FARMING = "pause_farming"
    PAUSE_PUBLISHING = "pause_publishing"
    PAUSE_COLLECTION = "pause_collection"
    PAUSE_INTERACTION = "pause_interaction"
    PAUSE_WORKFLOW = "pause_workflow"
    RETRY_APPROVED_JOB = "retry_approved_job"
    CANCEL_JOB = "cancel_job"
    TRIGGER_HEALTH_CHECK = "trigger_health_check"
    ACKNOWLEDGE_ALERT = "acknowledge_alert"
    OPEN_INCIDENT = "open_incident"
    CLOSE_INCIDENT = "close_incident"
    WORKSPACE_PAUSE = "workspace_pause"
    FEATURE_PAUSE = "feature_pause"
    KILL_SWITCH = "kill_switch"


HIGH_RISK_ACTIONS = frozenset(
    {
        ActionKind.RESUME_ACCOUNT,
        ActionKind.RECOVER_BROWSER,
        ActionKind.ROTATE_PROXY_REFERENCE,
        ActionKind.RETRY_APPROVED_JOB,
        ActionKind.CLOSE_INCIDENT,
        ActionKind.KILL_SWITCH,
    }
)


@dataclass(frozen=True, slots=True)
class OperationsScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:operations:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets and session material must use encrypted references.")


@dataclass(slots=True)
class OperationsCenter:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    status: OperationsStatus = OperationsStatus.DRAFT
    mode: str = "supervised"
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Operations center identity and scope are required.")
        if self.version < 1 or self.mode not in {"observe", "supervised", "manual"}:
            raise ValueError("Version and a bounded operations mode are required.")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class OperationsTask:
    id: str
    tenant: str
    workspace: str
    kind: str
    owner: str
    priority: int = 50
    status: TaskStatus = TaskStatus.QUEUED
    timeout_seconds: int = 300
    retry_count: int = 0
    maximum_retries: int = 0
    approved: bool = False

    def validate(self) -> None:
        if not self.id or not self.kind or not self.owner:
            raise ValueError("Task identity, kind, and owner are required.")
        if not 0 <= self.priority <= 100 or not 1 <= self.timeout_seconds <= 86400:
            raise ValueError("Task priority or timeout is outside the bounded range.")
        if not 0 <= self.maximum_retries <= 10:
            raise ValueError("Maximum retries must be within [0, 10].")


@dataclass(slots=True)
class OperationsAlert:
    id: str
    tenant: str
    workspace: str
    severity: str
    category: str
    source_module: str
    message: str
    account_reference: str = ""
    status: AlertStatus = AlertStatus.OPEN
    acknowledgement: str = ""
    escalation: str = ""
    resolution: str = ""
    history: list[str] = field(default_factory=list)


@dataclass(slots=True)
class OperationsIncident:
    id: str
    tenant: str
    workspace: str
    title: str
    description: str
    priority: str
    impact: str
    source: str
    owner: str
    status: IncidentStatus = IncidentStatus.OPEN
    related_accounts: list[str] = field(default_factory=list)
    related_workflows: list[str] = field(default_factory=list)
    related_jobs: list[str] = field(default_factory=list)
    timeline: list[str] = field(default_factory=list)
    resolution: str = ""
    recovery_plan: str = ""
    postmortem_reference: str = ""


@dataclass(slots=True)
class HealthSnapshot:
    tenant: str
    workspace: str
    scores: dict[str, float]
    composite_platform_health: float
    last_check: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RecoveryRequest:
    id: str
    tenant: str
    workspace: str
    resource_kind: str
    resource_reference: str
    recovery_reference: str
    cooldown_seconds: int = 300
    maximum_attempts: int = 3
    manual_approval: bool = True
    attempts: int = 0
    outcome: str = "pending"
    restriction_active: bool = False
    challenge_unresolved: bool = False

    def validate(self) -> None:
        if not all((self.id, self.resource_kind, self.resource_reference)):
            raise ValueError("Recovery identity and resource are required.")
        if not 0 <= self.cooldown_seconds <= 86400:
            raise ValueError("Recovery cooldown is outside the bounded range.")
        if not 1 <= self.maximum_attempts <= 10:
            raise ValueError("Recovery attempts must be within [1, 10].")


@dataclass(slots=True)
class Approval:
    id: str
    tenant: str
    workspace: str
    action: ActionKind
    resource_reference: str
    approved_by: str
    expires_at: datetime


@dataclass(slots=True)
class AuditRecord:
    actor: str
    action: str
    resource: str
    tenant: str
    workspace: str
    reason: str
    before_state_reference: str = ""
    after_state_reference: str = ""
    approval_reference: str = ""
    correlation_id: str = ""
    timestamp: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ActivityEntry:
    tenant: str
    workspace: str
    category: str
    message: str
    actor: str
    correlation_id: str
    timestamp: datetime = field(default_factory=utcnow)
