"""Domain models for the enterprise TikTok AI Interaction Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ReviewStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TemplateKind(str, Enum):
    REPLY = "reply"
    COMMENT = "comment"
    MESSAGE = "message"


class QueueKind(str, Enum):
    PRIORITY = "priority"
    WORKSPACE = "workspace"
    RETRY = "retry"
    DELAYED = "delayed"


@dataclass(frozen=True, slots=True)
class InteractionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:interaction:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class InteractionProject:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    status: Lifecycle = Lifecycle.DRAFT
    priority: Priority = Priority.NORMAL
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Project identity, scope, and owner are required.")
        if self.version < 1:
            raise ValueError("Project version must be positive.")
        forbidden = {"password", "secret", "token", "cookie", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Project metadata cannot contain secrets.")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["priority"] = self.priority.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class DraftVersion:
    version: int
    content: str
    variables: dict[str, str]
    actor: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class InteractionDraft:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    content: str
    template_reference: str = ""
    language: str = "en"
    variables: dict[str, str] = field(default_factory=dict)
    review_status: ReviewStatus = ReviewStatus.NOT_REQUESTED
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    version: int = 1
    history: list[DraftVersion] = field(default_factory=list)

    def validate(self) -> None:
        if not self.content.strip() or not self.language.strip():
            raise ValueError("Draft content and language are required.")


@dataclass(slots=True)
class InteractionTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: TemplateKind
    localized_content: dict[str, str]
    variables: set[str] = field(default_factory=set)
    version: int = 1
    imported: bool = False

    def validate(self) -> None:
        if not self.name or not self.localized_content:
            raise ValueError("Template name and localization are required.")


@dataclass(slots=True)
class ReviewRecord:
    id: str
    draft_reference: str
    tenant: str
    workspace: str
    reviewer: str
    status: ReviewStatus = ReviewStatus.PENDING
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    notes: str = ""
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class InteractionTask:
    id: str
    project_reference: str
    draft_reference: str
    tenant: str
    workspace: str
    priority: int = 50
    status: Lifecycle = Lifecycle.DRAFT
    queue: QueueKind = QueueKind.WORKSPACE
    maximum_retries: int = 3
    attempts: int = 0
    scheduled_for: datetime | None = None
    failure_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)
    queued_at: datetime | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def validate(self) -> None:
        if not 0 <= self.priority <= 100:
            raise ValueError("Priority must be within [0, 100].")
        if not 0 <= self.maximum_retries <= 10:
            raise ValueError("Maximum retries must be within [0, 10].")


@dataclass(slots=True)
class Notification:
    kind: str
    resource: str
    tenant: str
    workspace: str
    message: str
    created_at: datetime = field(default_factory=utcnow)
