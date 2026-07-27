"""Typed contracts for bounded TikTok account-farming orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, time, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlanStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    READY = "ready"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class FarmingMode(str, Enum):
    MANUAL_ASSISTED = "manual_assisted"
    SCHEDULED = "scheduled"
    EVENT_TRIGGERED = "event_triggered"
    SIMULATION = "simulation"
    DRY_RUN = "dry_run"
    SUPERVISED_AUTOMATION = "supervised_automation"


class BehaviorCategory(str, Enum):
    FEED_BROWSING = "feed_browsing"
    SEARCH_BROWSING = "search_browsing"
    VIDEO_VIEWING = "video_viewing"
    PROFILE_VIEWING = "profile_viewing"
    CONTENT_SAVING_INTERFACE = "content_saving_interface"
    LIKE_ACTION_INTERFACE = "like_action_interface"
    FOLLOW_ACTION_INTERFACE = "follow_action_interface"
    COMMENT_DRAFT_INTERFACE = "comment_draft_interface"
    SHARE_DRAFT_INTERFACE = "share_draft_interface"


class ScheduleKind(str, Enum):
    MANUAL = "manual"
    INTERVAL = "interval"
    CALENDAR_WINDOW = "calendar_window"
    ONE_TIME = "one_time"
    RECURRING = "recurring"


class MissedRunPolicy(str, Enum):
    SKIP = "skip"
    RUN_ONCE = "run_once"
    REQUIRE_REVIEW = "require_review"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalKind(str, Enum):
    ACCOUNT_HEALTH = "account_health"
    LOGIN_HEALTH = "login_health"
    SESSION_HEALTH = "session_health"
    PROXY_HEALTH = "proxy_health"
    BROWSER_HEALTH = "browser_health"
    RESTRICTION = "restriction_signal"
    CHALLENGE = "challenge_signal"
    RATE_LIMIT = "rate_limit_signal"
    FAILURE_TREND = "failure_trend"


HIGH_RISK_BEHAVIORS = frozenset(
    {
        BehaviorCategory.LIKE_ACTION_INTERFACE,
        BehaviorCategory.FOLLOW_ACTION_INTERFACE,
        BehaviorCategory.COMMENT_DRAFT_INTERFACE,
        BehaviorCategory.SHARE_DRAFT_INTERFACE,
    }
)


@dataclass(frozen=True, slots=True)
class FarmingScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:farming:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Bounds:
    minimum: int
    maximum: int

    def validate(self, name: str, *, ceiling: int) -> None:
        if self.minimum < 0 or self.maximum < self.minimum or self.maximum > ceiling:
            raise ValueError(f"{name} must be bounded within [0, {ceiling}].")


@dataclass(slots=True)
class BehaviorProfile:
    id: str
    tenant: str
    workspace: str
    name: str
    behaviors: set[BehaviorCategory] = field(default_factory=set)
    session_duration_seconds: Bounds = field(default_factory=lambda: Bounds(60, 900))
    action_count: Bounds = field(default_factory=lambda: Bounds(0, 10))
    navigation_count: Bounds = field(default_factory=lambda: Bounds(1, 30))
    idle_interval_seconds: Bounds = field(default_factory=lambda: Bounds(5, 120))
    daily_limit: int = 30
    weekly_limit: int = 150
    cooldown_seconds: int = 300
    allowed_time_windows: list[tuple[time, time]] = field(default_factory=list)
    timezone: str = "UTC"
    country_reference: str = ""
    device_profile_reference: str = ""
    proxy_binding_reference: str = ""

    def validate(self) -> None:
        if not self.id or not self.name or not self.timezone:
            raise ValueError("Profile ID, name, and timezone are required.")
        self.session_duration_seconds.validate("Session duration", ceiling=14_400)
        self.action_count.validate("Action count", ceiling=100)
        self.navigation_count.validate("Navigation count", ceiling=500)
        self.idle_interval_seconds.validate("Idle interval", ceiling=3_600)
        if not 0 < self.daily_limit <= 500:
            raise ValueError("Daily limit must be within [1, 500].")
        if not self.daily_limit <= self.weekly_limit <= 3_500:
            raise ValueError("Weekly limit must be bounded and cover daily limit.")
        if not 0 <= self.cooldown_seconds <= 86_400:
            raise ValueError("Cooldown must be within [0, 86400].")
        if len(self.allowed_time_windows) > 24:
            raise ValueError("At most 24 allowed time windows are supported.")


@dataclass(slots=True)
class FarmingPlan:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    account_references: list[str]
    profile_reference: str
    priority: int = 0
    mode: FarmingMode = FarmingMode.MANUAL_ASSISTED
    status: PlanStatus = PlanStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.tenant,
                self.workspace,
                self.owner,
                self.profile_reference,
            )
        ):
            raise ValueError("Plan identity, scope, owner, and profile are required.")
        if not self.account_references or len(self.account_references) > 100:
            raise ValueError("Plans require between 1 and 100 account references.")
        if len(set(self.account_references)) != len(self.account_references):
            raise ValueError("Account references must be unique.")
        if not 0 <= self.priority <= 100 or self.version < 1:
            raise ValueError("Plan priority or version is out of bounds.")
        forbidden = {"cookie", "session", "password", "secret", "token", "credential"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Plan metadata cannot contain secrets.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["mode"] = self.mode.value
        result["status"] = self.status.value
        result["created_at"] = self.created_at.isoformat()
        result["updated_at"] = self.updated_at.isoformat()
        return result


@dataclass(slots=True)
class FarmingSchedule:
    id: str
    plan_reference: str
    tenant: str
    workspace: str
    kind: ScheduleKind
    timezone: str = "UTC"
    interval_seconds: int = 0
    missed_run_policy: MissedRunPolicy = MissedRunPolicy.SKIP
    maximum_runs: int = 1
    start_date: datetime | None = None
    end_date: datetime | None = None
    runs: int = 0

    def validate(self) -> None:
        if not self.id or not self.plan_reference or not self.timezone:
            raise ValueError("Schedule ID, plan, and timezone are required.")
        if not 1 <= self.maximum_runs <= 10_000:
            raise ValueError("Maximum runs must be within [1, 10000].")
        if (
            self.kind is ScheduleKind.INTERVAL
            and not 60 <= self.interval_seconds <= 604_800
        ):
            raise ValueError("Interval schedules must be within [60, 604800] seconds.")
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("Schedule end date must not precede its start date.")


@dataclass(slots=True)
class ResourceLimits:
    per_account: int = 1
    per_workspace: int = 20
    per_device: int = 1
    per_proxy: int = 3
    per_session: int = 25
    daily: int = 100
    weekly: int = 500
    concurrency: int = 5
    navigation_timeout_seconds: int = 30
    execution_timeout_seconds: int = 1_800

    def validate(self) -> None:
        values = asdict(self)
        ceilings = {
            "per_account": 10,
            "per_workspace": 1_000,
            "per_device": 10,
            "per_proxy": 25,
            "per_session": 500,
            "daily": 10_000,
            "weekly": 50_000,
            "concurrency": 100,
            "navigation_timeout_seconds": 300,
            "execution_timeout_seconds": 14_400,
        }
        for key, value in values.items():
            if not 1 <= value <= ceilings[key]:
                raise ValueError(f"{key} must be bounded within [1, {ceilings[key]}].")


@dataclass(slots=True)
class Approval:
    id: str
    plan_reference: str
    tenant: str
    workspace: str
    requested_by: str
    execution_scope: set[BehaviorCategory]
    approval_required: bool = True
    reviewer: str = ""
    approval_notes: str = ""
    expiration: datetime | None = None
    rejection_reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING


@dataclass(slots=True)
class HealthSignal:
    id: str
    tenant: str
    workspace: str
    account_reference: str
    kind: SignalKind
    value: float
    confidence: float
    reason: str = ""
    occurred_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not 0 <= self.value <= 100 or not 0 <= self.confidence <= 1:
            raise ValueError("Signal value and confidence must be normalized.")


@dataclass(slots=True)
class RiskScore:
    account_reference: str
    level: RiskLevel
    risk_factors: list[str]
    score: float
    reason: str
    recommended_action: str
    auto_pause_threshold: float = 80
    manual_review_threshold: float = 50


@dataclass(slots=True)
class Recommendation:
    id: str
    plan_reference: str
    suggested_schedule: str
    suggested_session_duration_seconds: int
    suggested_cooldown_seconds: int
    suggested_action_bounds: Bounds
    suggested_pause: bool
    supporting_signals: list[str]
    confidence: float
    advisory_only: bool = True


@dataclass(slots=True)
class Execution:
    id: str
    plan_reference: str
    tenant: str
    workspace: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    checkpoint: str = ""
    attempts: int = 0
    maximum_attempts: int = 3
    outcome: dict[str, Any] = field(default_factory=dict)
    started_at: datetime | None = None
    finished_at: datetime | None = None
