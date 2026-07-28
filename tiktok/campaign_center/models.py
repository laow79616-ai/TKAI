"""Domain contracts for the Enterprise TikTok Campaign Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from re import fullmatch
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


FORBIDDEN_KEYS = {"password", "secret", "token", "cookie", "credential"}


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    REVIEW = "review"
    APPROVED = "approved"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class CampaignObjective(str, Enum):
    BRAND_AWARENESS = "brand_awareness"
    TRAFFIC = "traffic"
    ENGAGEMENT = "engagement"
    LEAD_COLLECTION = "lead_collection"
    PRODUCT_PROMOTION = "product_promotion"
    CUSTOM = "custom"


class CampaignPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ScheduleKind(str, Enum):
    IMMEDIATE = "immediate"
    ONE_TIME = "one_time"
    RECURRING = "recurring"
    CALENDAR = "calendar"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class CampaignScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:campaign:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Campaign:
    id: str
    name: str
    description: str
    workspace: str
    owner: str
    objective: CampaignObjective
    tenant: str
    priority: CampaignPriority = CampaignPriority.NORMAL
    status: CampaignStatus = CampaignStatus.DRAFT
    version: int = 1
    custom_objective_reference: str = ""
    audience_references: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.workspace, self.owner, self.tenant)):
            raise ValueError("Campaign identity, owner, and scope are required.")
        if self.version < 1:
            raise ValueError("Campaign version must be positive.")
        if self.objective is CampaignObjective.CUSTOM and not (
            self.custom_objective_reference
        ):
            raise ValueError("Custom campaigns require an objective reference.")
        _reject_secrets(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["objective"] = self.objective.value
        value["priority"] = self.priority.value
        value["status"] = self.status.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class CampaignPlan:
    id: str
    campaign_id: str
    tenant: str
    workspace: str
    publishing_reference: str = ""
    workflow_reference: str = ""
    automation_reference: str = ""
    execution_reference: str = ""
    content_references: list[str] = field(default_factory=list)
    schedule_reference: str = ""
    dependencies: list[str] = field(default_factory=list)
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all((self.id, self.campaign_id, self.tenant, self.workspace)):
            raise ValueError("Plan identity, campaign, and scope are required.")
        if not any(
            (
                self.publishing_reference,
                self.workflow_reference,
                self.automation_reference,
                self.execution_reference,
                self.content_references,
            )
        ):
            raise ValueError("A plan requires at least one bounded reference.")
        for reference in (
            self.publishing_reference,
            self.workflow_reference,
            self.automation_reference,
            self.execution_reference,
            self.schedule_reference,
            *self.content_references,
            *self.dependencies,
        ):
            _validate_reference(reference)
        _reject_secrets(self.metadata)


@dataclass(slots=True)
class CampaignSchedule:
    id: str
    campaign_id: str
    tenant: str
    workspace: str
    kind: ScheduleKind
    timezone_name: str
    starts_at: datetime | None = None
    recurrence: str = ""
    execution_window_seconds: int = 3600
    calendar_reference: str = ""

    def validate(self) -> None:
        if not all(
            (self.id, self.campaign_id, self.tenant, self.workspace, self.timezone_name)
        ):
            raise ValueError(
                "Schedule identity, campaign, scope, and timezone required."
            )
        if not fullmatch(r"[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)*", self.timezone_name):
            raise ValueError("Timezone must be an IANA-style timezone name.")
        if self.execution_window_seconds <= 0:
            raise ValueError("Execution window must be positive.")
        if self.kind is ScheduleKind.ONE_TIME and self.starts_at is None:
            raise ValueError("One-time schedules require a start time.")
        if self.kind is ScheduleKind.RECURRING and not self.recurrence:
            raise ValueError("Recurring schedules require a recurrence expression.")
        if self.kind is ScheduleKind.CALENDAR:
            _validate_reference(self.calendar_reference)


@dataclass(slots=True)
class CampaignApproval:
    id: str
    campaign_id: str
    tenant: str
    workspace: str
    reviewer: str
    status: ApprovalStatus = ApprovalStatus.PENDING
    notes: str = ""
    expires_at: datetime | None = None
    requested_at: datetime = field(default_factory=utcnow)
    decided_at: datetime | None = None

    @property
    def active(self) -> bool:
        return self.status is ApprovalStatus.APPROVED and (
            self.expires_at is None or self.expires_at > utcnow()
        )


@dataclass(frozen=True, slots=True)
class CampaignHealth:
    campaign_id: str
    campaign_health: str
    publishing_status: str
    workflow_status: str
    execution_status: str
    risk_status: str
    runtime_status: str
    checked_at: datetime


def _validate_reference(reference: str) -> None:
    if reference and not reference.startswith(("ref://", "kms://", "vault://")):
        raise ValueError("External references must be encrypted or opaque references.")


def _reject_secrets(value: dict[str, Any]) -> None:
    if FORBIDDEN_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are not permitted in campaign metadata.")
