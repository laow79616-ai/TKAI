"""Domain models for enterprise human and agent collaboration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkspaceStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class SessionStatus(str, Enum):
    OPEN = "open"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class PresenceStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    BUSY = "busy"
    IDLE = "idle"
    TYPING = "typing"
    AGENT_ACTIVE = "agent_active"


class TaskStatus(str, Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    REVIEW = "review"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HandoffType(str, Enum):
    HUMAN_TO_AGENT = "human_to_agent"
    AGENT_TO_HUMAN = "agent_to_human"
    AGENT_TO_AGENT = "agent_to_agent"
    WORKFLOW_TO_AGENT = "workflow_to_agent"


@dataclass(frozen=True, slots=True)
class CollaborationScope:
    tenant: str
    workspace: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Workspace:
    id: str
    tenant: str
    organization: str
    name: str
    description: str = ""
    members: tuple[str, ...] = ()
    roles: dict[str, str] = field(default_factory=dict)
    status: WorkspaceStatus = WorkspaceStatus.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Project:
    id: str
    tenant: str
    workspace: str
    owner: str
    applications: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    knowledge: tuple[str, ...] = ()
    workflow: str | None = None
    status: ProjectStatus = ProjectStatus.DRAFT
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class SharedContext:
    variables: dict[str, Any] = field(default_factory=dict)
    artifacts: tuple[dict[str, Any], ...] = ()
    knowledge_references: tuple[str, ...] = ()
    application_state: dict[str, Any] = field(default_factory=dict)
    workflow_state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CollaborationSession:
    id: str
    tenant: str
    workspace: str
    participants: tuple[str, ...] = ()
    agent_participants: tuple[str, ...] = ()
    shared_context: SharedContext = field(default_factory=SharedContext)
    shared_memory_namespace: str = "default"
    timeline: tuple[str, ...] = ()
    status: SessionStatus = SessionStatus.OPEN

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Message:
    id: str
    tenant: str
    workspace: str
    session_id: str
    thread_id: str
    sender: str
    body: str
    mentions: tuple[str, ...] = ()
    reply_to: str | None = None
    attachments: tuple[dict[str, Any], ...] = ()
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CollaborationTask:
    id: str
    tenant: str
    workspace: str
    title: str
    assignment: str | None = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.TODO
    due_date: str | None = None
    dependencies: tuple[str, ...] = ()
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["priority"] = self.priority.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class TimelineEvent:
    id: str
    tenant: str
    workspace: str
    actor: str
    category: str
    action: str
    resource: str
    details: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Handoff:
    id: str
    tenant: str
    workspace: str
    source: str
    target: str
    type: HandoffType
    context: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Notification:
    id: str
    tenant: str
    workspace: str
    recipient: str
    type: str
    message: str
    read: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
