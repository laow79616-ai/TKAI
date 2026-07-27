"""Domain contracts for the enterprise TikTok AI Content Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    EDITING = "editing"
    READY = "ready"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MediaType(str, Enum):
    VIDEO = "video"
    IMAGE = "image"
    AUDIO = "audio"
    SUBTITLE = "subtitle"
    THUMBNAIL = "thumbnail"


class ReviewStatus(str, Enum):
    NOT_REQUESTED = "not_requested"
    PENDING = "pending"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"


class ApprovalStatus(str, Enum):
    NOT_REQUIRED = "not_required"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class CaptionMode(str, Enum):
    MANUAL = "manual"
    AI_GENERATED = "ai_generated"
    TEMPLATE_BASED = "template_based"


class HashtagSource(str, Enum):
    MANUAL = "manual"
    SUGGESTED = "suggested"


class QueueMode(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"


class QueueStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScheduleKind(str, Enum):
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class MissedRunPolicy(str, Enum):
    SKIP = "skip"
    RUN_ONCE = "run_once"
    RESCHEDULE = "reschedule"


class TemplateKind(str, Enum):
    CAPTION = "caption"
    HASHTAG = "hashtag"
    PUBLISHING = "publishing"
    PROJECT = "project"


@dataclass(frozen=True, slots=True)
class ContentScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:content:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ContentProject:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    category: str
    status: ProjectStatus = ProjectStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (self.id, self.name, self.tenant, self.workspace, self.owner, self.category)
        ):
            raise ValueError(
                "Project identity, scope, owner, and category are required."
            )
        if self.version < 1:
            raise ValueError("Project version must be positive.")
        forbidden = {"password", "secret", "token", "cookie", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Project metadata cannot contain secrets.")

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class MediaAsset:
    id: str
    tenant: str
    workspace: str
    name: str
    media_type: MediaType
    checksum: str
    encrypted_storage_reference: str
    folder: str = ""
    tags: set[str] = field(default_factory=set)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.tenant,
                self.workspace,
                self.name,
                self.checksum,
                self.encrypted_storage_reference,
            )
        ):
            raise ValueError(
                "Media identity, scope, checksum, and storage are required."
            )
        if not self.encrypted_storage_reference.startswith(("kms://", "vault://")):
            raise ValueError("Media must use an encrypted storage reference.")


@dataclass(slots=True)
class DraftVersion:
    version: int
    content: dict[str, Any]
    created_by: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ContentDraft:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    title: str
    media_references: list[str] = field(default_factory=list)
    version: int = 1
    versions: list[DraftVersion] = field(default_factory=list)
    review_status: ReviewStatus = ReviewStatus.NOT_REQUESTED
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED
    archived: bool = False


@dataclass(slots=True)
class Caption:
    id: str
    draft_reference: str
    tenant: str
    workspace: str
    text: str
    mode: CaptionMode = CaptionMode.MANUAL
    variables: dict[str, str] = field(default_factory=dict)
    locale: str = "en"
    maximum_characters: int = 2200
    template_reference: str = ""

    @property
    def character_count(self) -> int:
        return len(self.text)

    def validate(self) -> None:
        if not self.text.strip() or self.character_count > self.maximum_characters:
            raise ValueError("Caption is empty or exceeds its character limit.")
        if self.mode is CaptionMode.TEMPLATE_BASED and not self.template_reference:
            raise ValueError("Template-based captions require a template.")


@dataclass(slots=True)
class HashtagSet:
    id: str
    tenant: str
    workspace: str
    name: str
    values: list[str]
    source: HashtagSource = HashtagSource.MANUAL
    favorite: bool = False
    collection: str = ""
    ranking_reference: str = ""

    def validate(self) -> None:
        normalized = [item.casefold() for item in self.values]
        if (
            not self.values
            or len(self.values) > 30
            or len(set(normalized)) != len(normalized)
        ):
            raise ValueError("Hashtags must contain 1-30 unique values.")
        if any(not item.startswith("#") or len(item) < 2 for item in self.values):
            raise ValueError("Hashtags must start with #.")


@dataclass(slots=True)
class Cover:
    id: str
    draft_reference: str
    tenant: str
    workspace: str
    encrypted_storage_reference: str
    crop: tuple[float, float, float, float] = (0, 0, 1, 1)
    template_reference: str = ""
    history: list[str] = field(default_factory=list)
    approval_status: ApprovalStatus = ApprovalStatus.NOT_REQUIRED

    def validate(self) -> None:
        if not self.encrypted_storage_reference.startswith(("kms://", "vault://")):
            raise ValueError("Cover must use an encrypted storage reference.")
        if any(value < 0 or value > 1 for value in self.crop):
            raise ValueError("Crop coordinates must be normalized.")


@dataclass(slots=True)
class PublishingSchedule:
    id: str
    project_reference: str
    tenant: str
    workspace: str
    kind: ScheduleKind
    timezone: str
    publishing_window: tuple[str, str]
    missed_run_policy: MissedRunPolicy = MissedRunPolicy.SKIP
    run_at: datetime | None = None
    recurrence: str = ""
    calendar_reference: str = ""

    def validate(self) -> None:
        if not self.timezone or len(self.publishing_window) != 2:
            raise ValueError("Timezone and publishing window are required.")
        if self.kind is ScheduleKind.ONE_TIME and self.run_at is None:
            raise ValueError("One-time schedules require run_at.")
        if self.kind is ScheduleKind.RECURRING and not self.recurrence:
            raise ValueError("Recurring schedules require a recurrence expression.")


@dataclass(slots=True)
class PublishJob:
    id: str
    project_reference: str
    draft_reference: str
    account_reference: str
    tenant: str
    workspace: str
    mode: QueueMode = QueueMode.IMMEDIATE
    priority: int = 50
    status: QueueStatus = QueueStatus.PENDING
    retries: int = 0
    maximum_retries: int = 3
    backoff_seconds: int = 30
    schedule_reference: str = ""
    failure_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def validate(self) -> None:
        if not 0 <= self.priority <= 100:
            raise ValueError("Priority must be within [0, 100].")
        if (
            not 0 <= self.maximum_retries <= 10
            or not 1 <= self.backoff_seconds <= 86400
        ):
            raise ValueError("Retry policy is out of bounds.")
        if self.mode is QueueMode.SCHEDULED and not self.schedule_reference:
            raise ValueError("Scheduled jobs require a schedule.")


@dataclass(slots=True)
class ContentTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: TemplateKind
    content: dict[str, Any]
    version: int = 1
    imported: bool = False
