"""Domain models for the bounded Enterprise TikTok Content Pipeline."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PipelineStatus(str, Enum):
    DRAFT = "draft"
    CONFIGURED = "configured"
    VALIDATING = "validating"
    READY = "ready"
    QUEUED = "queued"
    PROCESSING = "processing"
    REVIEW = "review"
    APPROVED = "approved"
    PACKAGED = "packaged"
    HANDED_OFF = "handed_off"
    COMPLETED = "completed"
    PAUSED = "paused"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class StageKind(str, Enum):
    INTAKE = "intake"
    METADATA_VALIDATION = "metadata_validation"
    MEDIA_VALIDATION = "media_validation"
    CONTENT_PREPARATION = "content_preparation"
    TRANSFORMATION = "transformation"
    QUALITY_EVALUATION = "quality_evaluation"
    COMPLIANCE_REVIEW = "compliance_review_reference"
    HUMAN_REVIEW = "human_review"
    APPROVAL = "approval"
    PACKAGING = "packaging"
    PUBLISHING_HANDOFF = "publishing_handoff"
    COMPLETION = "completion"


class JobKind(str, Enum):
    PIPELINE = "pipeline"
    STAGE = "stage"
    VALIDATION = "validation"
    TRANSFORMATION = "transformation"
    REVIEW = "review"
    PACKAGING = "packaging"
    HANDOFF = "handoff"
    RECOVERY = "recovery"


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ApprovalKind(str, Enum):
    CONTENT = "content"
    CAMPAIGN = "campaign"
    PUBLISHING_HANDOFF = "publishing_handoff"
    HIGH_RISK = "high_risk_review_reference"


class HandoffTarget(str, Enum):
    CREATOR_WORKSPACE = "creator_workspace"
    CAMPAIGN_CENTER = "campaign_center"
    CONTENT_CENTER = "content_center"
    PUBLISHING_CENTER = "publishing_center"
    WORKFLOW_CENTER = "workflow_center"
    AUTOMATION_ENGINE = "automation_engine"
    TASK_SCHEDULER = "task_scheduler"
    EXECUTION_ENGINE = "execution_engine_reference"


@dataclass(frozen=True, slots=True)
class RequestScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:content-pipeline:read"})


def validate_metadata(value: dict[str, Any]) -> None:
    forbidden = {
        "password",
        "secret",
        "token",
        "cookie",
        "credential",
        "session",
        "proxy",
    }
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in pipeline metadata.")
    if len(str(value)) > 16_384:
        raise ValueError("Metadata exceeds the bounded payload limit.")


def validate_reference(value: str) -> None:
    allowed = (
        "encrypted://",
        "ref://",
        "content://",
        "campaign://",
        "workspace://",
        "schedule://",
        "account://",
        "policy://",
    )
    if not value.startswith(allowed):
        raise ValueError("Only encrypted or opaque references are accepted.")
    if len(value) > 2048:
        raise ValueError("Reference exceeds the bounded payload limit.")


@dataclass(slots=True)
class PipelineInput:
    video_reference: str = ""
    image_reference: str = ""
    audio_reference: str = ""
    subtitle_reference: str = ""
    thumbnail_reference: str = ""
    caption_reference: str = ""
    hashtag_reference: str = ""
    template_reference: str = ""
    campaign_reference: str = ""

    def validate(self) -> None:
        values = [value for value in asdict(self).values() if value]
        if not values:
            raise ValueError("At least one encrypted pipeline input is required.")
        for value in values:
            validate_reference(value)


@dataclass(slots=True)
class ContentPipeline:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    project_reference: str
    campaign_reference: str
    priority: int = 50
    status: PipelineStatus = PipelineStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    inputs: PipelineInput = field(default_factory=PipelineInput)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Pipeline identity and isolation scope are required.")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be within [1, 100].")
        validate_reference(self.project_reference)
        validate_reference(self.campaign_reference)
        validate_metadata(self.metadata)
        self.inputs.validate()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class PipelineJob:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    kind: JobKind
    stage: StageKind
    priority: int = 50
    status: JobStatus = JobStatus.QUEUED
    retry: int = 0
    maximum_attempts: int = 3
    timeout_seconds: int = 300
    created_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None


@dataclass(slots=True)
class ValidationResult:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    valid: bool
    checks: dict[str, bool]
    explanation: list[str]


@dataclass(slots=True)
class QualityResult:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    completeness_score: float
    metadata_quality: float
    reference_health: float
    caption_quality_reference: float
    hashtag_quality_reference: float
    subtitle_coverage: float
    thumbnail_availability: float
    readiness_score: float
    explanation: list[str]
    threshold: float = 0.75


@dataclass(slots=True)
class Review:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    reviewer: str
    status: ReviewStatus
    notes: str
    requested_changes: list[str]
    automated_review_reference: str
    expires_at: datetime
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Approval:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    kind: ApprovalKind
    reviewer: str
    approved: bool
    notes: str
    expires_at: datetime
    rejection_reason: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class ContentPackage:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    media_references: list[str]
    caption: str
    hashtags: list[str]
    subtitle_reference: str
    thumbnail_reference: str
    publishing_settings_reference: str
    schedule_reference: str
    account_reference: str
    campaign_reference: str
    version: int
    checksum_manifest: dict[str, str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Handoff:
    id: str
    pipeline_id: str
    package_reference: str
    tenant: str
    workspace: str
    target: HandoffTarget
    receipt_reference: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Checkpoint:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    pipeline_state: PipelineStatus
    completed_stages: list[StageKind]
    pending_stages: list[StageKind]
    job_references: list[str]
    approval_references: list[str]
    package_reference: str
    retry_position: int
    integrity_hash: str
    expires_at: datetime


@dataclass(slots=True)
class SafetyState:
    restriction_active: bool = False
    challenge_active: bool = False
    workspace_paused: bool = False
    account_paused: bool = False
    kill_switch: bool = False


@dataclass(slots=True)
class AuditEvent:
    pipeline_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
