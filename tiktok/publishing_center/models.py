"""Domain models for the enterprise TikTok AI Publishing Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PublishingStatus(str, Enum):
    DRAFT = "draft"
    APPROVED = "approved"
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ScheduleMode(str, Enum):
    IMMEDIATE = "immediate"
    SCHEDULED = "scheduled"
    RECURRING = "recurring"
    CALENDAR_WINDOW = "calendar_window"


class MissedSchedulePolicy(str, Enum):
    SKIP = "skip"
    RUN_IMMEDIATELY = "run_immediately"
    RESCHEDULE = "reschedule"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class FailureCategory(str, Enum):
    VALIDATION = "validation"
    MEDIA = "media"
    BROWSER = "browser"
    PROXY = "proxy"
    SESSION = "session"
    TIMEOUT = "timeout"
    CANCELLATION = "cancellation"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class PublishingScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:publishing:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace and actor are required.")


@dataclass(slots=True)
class PublishingSchedule:
    mode: ScheduleMode = ScheduleMode.IMMEDIATE
    run_at: datetime | None = None
    recurrence: str = ""
    timezone: str = "UTC"
    publishing_window: tuple[str, str] | None = None
    calendar_reference: str = ""
    maximum_parallel_jobs: int = 1
    missed_policy: MissedSchedulePolicy = MissedSchedulePolicy.SKIP

    def validate(self) -> None:
        if self.timezone != "UTC":
            try:
                ZoneInfo(self.timezone)
            except ZoneInfoNotFoundError as exc:
                raise ValueError(f"Unknown timezone: {self.timezone}") from exc
        if not 1 <= self.maximum_parallel_jobs <= 100:
            raise ValueError("Maximum parallel jobs must be within [1, 100].")
        if self.mode is ScheduleMode.SCHEDULED and self.run_at is None:
            raise ValueError("Scheduled jobs require run_at.")
        if self.mode is ScheduleMode.RECURRING and not self.recurrence:
            raise ValueError("Recurring jobs require a recurrence expression.")
        if self.mode is ScheduleMode.CALENDAR_WINDOW and (
            not self.calendar_reference or self.publishing_window is None
        ):
            raise ValueError("Calendar-window jobs require calendar and window.")


@dataclass(slots=True)
class RetryPolicy:
    maximum_attempts: int = 3
    retry_delay_seconds: int = 30
    exponential_backoff: bool = True
    auto_retry: bool = True
    retryable_categories: frozenset[FailureCategory] = frozenset(
        {
            FailureCategory.BROWSER,
            FailureCategory.PROXY,
            FailureCategory.SESSION,
            FailureCategory.TIMEOUT,
            FailureCategory.UNKNOWN,
        }
    )

    def validate(self) -> None:
        if not 1 <= self.maximum_attempts <= 10:
            raise ValueError("Maximum attempts must be within [1, 10].")
        if not 1 <= self.retry_delay_seconds <= 86400:
            raise ValueError("Retry delay must be within [1, 86400].")

    def delay_for(self, attempt: int) -> int:
        multiplier = 2 ** max(attempt - 1, 0) if self.exponential_backoff else 1
        return min(self.retry_delay_seconds * multiplier, 86400)


@dataclass(slots=True)
class PublishingJob:
    id: str
    name: str
    project_reference: str
    account_reference: str
    media_reference: str
    tenant: str
    workspace: str
    publisher: str
    priority: int = 50
    status: PublishingStatus = PublishingStatus.DRAFT
    schedule: PublishingSchedule = field(default_factory=PublishingSchedule)
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    metadata: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0
    version: int = 1
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)
    next_attempt_at: datetime | None = None

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.project_reference,
                self.account_reference,
                self.media_reference,
                self.tenant,
                self.workspace,
                self.publisher,
            )
        ):
            raise ValueError("Publishing job identity and references are required.")
        if not 0 <= self.priority <= 100:
            raise ValueError("Priority must be within [0, 100].")
        forbidden = {"password", "secret", "token", "cookie", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Publishing metadata cannot contain secrets.")
        self.schedule.validate()
        self.retry_policy.validate()

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        result["schedule"]["mode"] = self.schedule.mode.value
        result["schedule"]["missed_policy"] = self.schedule.missed_policy.value
        result["retry_policy"]["retryable_categories"] = sorted(
            item.value for item in self.retry_policy.retryable_categories
        )
        for name in ("created_at", "updated_at", "next_attempt_at"):
            value = result[name]
            result[name] = value.isoformat() if value else None
        run_at = result["schedule"]["run_at"]
        result["schedule"]["run_at"] = run_at.isoformat() if run_at else None
        return result


@dataclass(slots=True)
class Approval:
    job_reference: str
    reviewer: str
    state: ApprovalState = ApprovalState.PENDING
    notes: str = ""
    expires_at: datetime | None = None
    reviewed_at: datetime | None = None
    version: int = 1


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    job_reference: str
    status: PublishingStatus
    operator: str
    version: int
    event: str
    timestamp: datetime = field(default_factory=utcnow)
    details: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FailureRecord:
    job_reference: str
    category: FailureCategory
    message: str
    recoverable: bool
    occurred_at: datetime = field(default_factory=utcnow)
    recovered_at: datetime | None = None
    recovered_by: str = ""
