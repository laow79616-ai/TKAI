"""Domain contracts for the Enterprise TikTok Creator Workspace."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from re import fullmatch
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


FORBIDDEN_METADATA_KEYS = {
    "password",
    "secret",
    "token",
    "cookie",
    "credential",
}


class WorkspaceStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    EDITING = "editing"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AssetKind(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    THUMBNAIL = "thumbnail"
    CAPTION = "caption"
    HASHTAG = "hashtag"


class CalendarKind(str, Enum):
    PUBLISHING = "publishing"
    REVIEW = "review"
    REMINDER = "reminder"


class TemplateKind(str, Enum):
    CAPTION = "caption"
    HASHTAG = "hashtag"
    PUBLISHING = "publishing"
    CAMPAIGN = "campaign"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalKind(str, Enum):
    PUBLISHING = "publishing"
    CAMPAIGN = "campaign"
    CONTENT = "content"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class CreatorScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:creator:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class CreatorWorkspace:
    id: str
    name: str
    description: str
    owner: str
    tenant: str
    workspace: str
    status: WorkspaceStatus = WorkspaceStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (self.id, self.name, self.owner, self.tenant, self.workspace)
        ):
            raise ValueError("Workspace identity, owner, and scope are required.")
        if self.version < 1:
            raise ValueError("Workspace version must be positive.")
        if FORBIDDEN_METADATA_KEYS & {key.casefold() for key in self.metadata}:
            raise ValueError("Secrets are not permitted in workspace metadata.")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class ContentProject:
    id: str
    creator_workspace_id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    campaign_reference: str = ""
    publishing_plan_reference: str = ""
    workflow_reference: str = ""
    priority: Priority = Priority.NORMAL
    schedule: datetime | None = None
    status: WorkspaceStatus = WorkspaceStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.creator_workspace_id,
                self.name,
                self.tenant,
                self.workspace,
                self.owner,
            )
        ):
            raise ValueError(
                "Project identity, workspace, owner, and scope are required."
            )
        if FORBIDDEN_METADATA_KEYS & {key.casefold() for key in self.metadata}:
            raise ValueError("Secrets are not permitted in project metadata.")


@dataclass(slots=True)
class CreativeAsset:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    name: str
    kind: AssetKind
    encrypted_reference: str
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.project_reference,
                self.tenant,
                self.workspace,
                self.name,
                self.encrypted_reference,
            )
        ):
            raise ValueError(
                "Asset identity, project, scope, and reference are required."
            )
        if not self.encrypted_reference.startswith(("kms://", "vault://")):
            raise ValueError("Assets require an encrypted reference.")
        if FORBIDDEN_METADATA_KEYS & {key.casefold() for key in self.metadata}:
            raise ValueError("Secrets are not permitted in asset metadata.")


@dataclass(slots=True)
class CalendarEntry:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    kind: CalendarKind
    starts_at: datetime
    timezone_name: str
    title: str
    reminder_minutes: int = 0
    created_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.project_reference,
                self.tenant,
                self.workspace,
                self.title,
                self.timezone_name,
            )
        ):
            raise ValueError(
                "Calendar identity, project, scope, and timezone are required."
            )
        if not fullmatch(r"[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)*", self.timezone_name):
            raise ValueError("Timezone must be an IANA-style timezone name.")
        if self.reminder_minutes < 0:
            raise ValueError("Reminder minutes cannot be negative.")


@dataclass(slots=True)
class CreatorTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: TemplateKind
    content: dict[str, Any]
    version: int = 1
    source_reference: str = ""

    def validate(self) -> None:
        if not all((self.id, self.tenant, self.workspace, self.name)):
            raise ValueError("Template identity, name, and scope are required.")
        if self.version < 1:
            raise ValueError("Template version must be positive.")
        if FORBIDDEN_METADATA_KEYS & {key.casefold() for key in self.content}:
            raise ValueError("Secrets are not permitted in templates.")


@dataclass(slots=True)
class Review:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    reviewer: str
    status: ReviewStatus = ReviewStatus.PENDING
    notes: str = ""
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    requested_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None
    history: list[dict[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class Approval:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    kind: ApprovalKind
    reviewer: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    expires_at: datetime | None = None
    notes: str = ""
    requested_at: datetime = field(default_factory=utcnow)
    decided_at: datetime | None = None

    @property
    def active(self) -> bool:
        return (
            self.status is ApprovalStatus.APPROVED
            and (self.expires_at is None or self.expires_at > utcnow())
        )


@dataclass(frozen=True, slots=True)
class PublishingPlanRequest:
    project_reference: str
    publishing_plan_reference: str
    tenant: str
    workspace: str
    requested_by: str
