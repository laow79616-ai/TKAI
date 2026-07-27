"""Validated domain models for the TikTok AI Risk Control Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Lifecycle(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    MONITORING = "monitoring"
    REVIEW_REQUIRED = "review_required"
    PAUSED = "paused"
    RECOVERING = "recovering"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SignalKind(str, Enum):
    LOGIN_FAILURE = "login_failure"
    COOKIE_EXPIRATION = "cookie_expiration"
    SESSION_EXPIRATION = "session_expiration"
    BROWSER_CRASH = "browser_crash"
    PROXY_FAILURE = "proxy_failure"
    PROXY_COUNTRY_MISMATCH = "proxy_country_mismatch"
    DEVICE_PROFILE_MISMATCH = "device_profile_mismatch"
    UNUSUAL_SCHEDULE = "unusual_schedule"
    ACTION_LIMIT_APPROACHING = "action_limit_approaching"
    RATE_LIMIT_SIGNAL = "rate_limit_signal"
    CHALLENGE_SIGNAL = "challenge_signal"
    RESTRICTION_SIGNAL = "restriction_signal"
    SUSPENSION_SIGNAL = "suspension_signal"
    BAN_SIGNAL = "ban_signal"
    PUBLISHING_FAILURE_TREND = "publishing_failure_trend"
    INTERACTION_FAILURE_TREND = "interaction_failure_trend"
    COLLECTION_FAILURE_TREND = "collection_failure_trend"


class PolicyKind(str, Enum):
    ACCOUNT = "account"
    BROWSER = "browser"
    PROXY = "proxy"
    PUBLISHING = "publishing"
    INTERACTION = "interaction"
    COLLECTION = "collection"
    SCHEDULE = "schedule"
    CONCURRENCY = "concurrency"
    APPROVAL = "approval"
    RECOVERY = "recovery"


class RuleOperator(str, Enum):
    SIGNAL_MATCH = "signal_match"
    THRESHOLD_MATCH = "threshold_match"
    TREND_MATCH = "trend_match"


class RiskAction(str, Enum):
    NOTIFY = "notify"
    REQUIRE_REVIEW = "require_review"
    REQUIRE_APPROVAL = "require_approval"
    PAUSE_ACCOUNT = "pause_account"
    PAUSE_WORKFLOW = "pause_workflow"
    PAUSE_PUBLISHING = "pause_publishing"
    PAUSE_INTERACTION = "pause_interaction"
    PAUSE_COLLECTION = "pause_collection"
    DRAIN_BROWSER = "drain_browser"
    RELEASE_PROXY = "release_proxy"
    TRIGGER_RECOVERY = "trigger_recovery"
    ESCALATE = "escalate"
    KILL_SWITCH = "kill_switch"


class ReviewDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class AlertStatus(str, Enum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


@dataclass(frozen=True, slots=True)
class RiskScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:risk:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


def validate_metadata(metadata: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "session", "credential"}
    if forbidden & {key.casefold() for key in metadata}:
        raise ValueError("Metadata cannot contain secrets, cookies, or sessions.")


@dataclass(slots=True)
class RiskProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    account_reference: str
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: float = 0.0
    status: Lifecycle = Lifecycle.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Profile identity, scope, and owner are required.")
        if not 0 <= self.risk_score <= 100:
            raise ValueError("Risk score must be within [0, 100].")
        if self.version < 1:
            raise ValueError("Version must be positive.")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["risk_level"] = self.risk_level.value
        value["status"] = self.status.value
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(slots=True)
class RiskSignal:
    id: str
    tenant: str
    workspace: str
    kind: SignalKind
    source: str
    severity: int
    confidence: float
    account_reference: str = ""
    occurred_at: datetime = field(default_factory=utcnow)
    evidence_references: tuple[str, ...] = ()

    def validate(self) -> None:
        if not self.id or not self.source:
            raise ValueError("Signal ID and source are required.")
        if not 1 <= self.severity <= 10:
            raise ValueError("Severity must be within [1, 10].")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be within [0, 1].")


@dataclass(slots=True)
class RiskPolicy:
    id: str
    tenant: str
    workspace: str
    name: str
    kind: PolicyKind
    enabled: bool = True
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id or not self.name or self.version < 1:
            raise ValueError("Valid policy identity, name, and version are required.")
        validate_metadata(self.metadata)


@dataclass(slots=True)
class RiskRule:
    id: str
    tenant: str
    workspace: str
    policy_reference: str
    operator: RuleOperator
    action: RiskAction
    signal_kind: SignalKind | None = None
    threshold: float = 0
    trend_count: int = 1
    window_seconds: int = 300
    priority: int = 50
    cooldown_seconds: int = 60
    version: int = 1
    enabled: bool = True

    def validate(self) -> None:
        if not self.id or not self.policy_reference:
            raise ValueError("Rule ID and policy reference are required.")
        if not 0 <= self.threshold <= 100:
            raise ValueError("Threshold must be within [0, 100].")
        if not 1 <= self.trend_count <= 1000:
            raise ValueError("Trend count must be within [1, 1000].")
        if not 1 <= self.window_seconds <= 2_592_000:
            raise ValueError("Time window must be within [1, 2592000] seconds.")
        if not 0 <= self.priority <= 100:
            raise ValueError("Priority must be within [0, 100].")
        if not 0 <= self.cooldown_seconds <= 604_800:
            raise ValueError("Cooldown must be within [0, 604800] seconds.")
        if self.version < 1:
            raise ValueError("Version must be positive.")


@dataclass(slots=True)
class RiskLimit:
    id: str
    tenant: str
    workspace: str
    scope_kind: str
    resource_reference: str
    per_hour: int = 100
    per_day: int = 1000
    concurrency: int = 5
    publishing_jobs: int = 100
    interaction_tasks: int = 100
    collection_jobs: int = 100

    def validate(self) -> None:
        values = (
            self.per_hour,
            self.per_day,
            self.concurrency,
            self.publishing_jobs,
            self.interaction_tasks,
            self.collection_jobs,
        )
        if not self.id or self.scope_kind not in {
            "account",
            "workspace",
            "browser",
            "proxy",
            "session",
        }:
            raise ValueError("A valid limit ID and scope are required.")
        if any(value < 0 or value > 1_000_000 for value in values):
            raise ValueError("Limits must be within [0, 1000000].")
        if self.concurrency > 1000:
            raise ValueError("Concurrency must be within [0, 1000].")


@dataclass(slots=True)
class Restriction:
    id: str
    tenant: str
    workspace: str
    feature: str
    reason: str
    account_reference: str = ""
    browser_reference: str = ""
    proxy_reference: str = ""
    schedule_reference: str = ""
    expires_at: datetime | None = None
    review_required: bool = True
    active: bool = True


@dataclass(slots=True)
class Pause:
    id: str
    tenant: str
    workspace: str
    kind: str
    target_reference: str
    reason: str
    manual: bool
    started_at: datetime = field(default_factory=utcnow)
    expires_at: datetime | None = None
    reviewer: str = ""
    resume_approval: str = ""
    active: bool = True


@dataclass(slots=True)
class RiskReview:
    id: str
    tenant: str
    workspace: str
    resource_reference: str
    reviewer: str
    evidence_references: tuple[str, ...] = ()
    decision: ReviewDecision = ReviewDecision.PENDING
    notes: str = ""
    expires_at: datetime | None = None


@dataclass(slots=True)
class HealthStatus:
    id: str
    tenant: str
    workspace: str
    account_reference: str
    account: float = 100
    login: float = 100
    session: float = 100
    browser: float = 100
    proxy: float = 100
    publishing: float = 100
    interaction: float = 100
    collection: float = 100
    composite: float = 100
    last_check: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        values = (
            self.account,
            self.login,
            self.session,
            self.browser,
            self.proxy,
            self.publishing,
            self.interaction,
            self.collection,
            self.composite,
        )
        if any(not 0 <= value <= 100 for value in values):
            raise ValueError("Health scores must be within [0, 100].")


@dataclass(slots=True)
class RiskScore:
    profile_reference: str
    score: float
    level: RiskLevel
    explanation: tuple[str, ...]
    recommended_action: RiskAction
    calculated_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Alert:
    id: str
    tenant: str
    workspace: str
    severity: RiskLevel
    source: str
    message: str
    account_reference: str = ""
    rule_reference: str = ""
    status: AlertStatus = AlertStatus.OPEN
    acknowledged_by: str = ""
    escalation: str = ""
    resolution: str = ""
    history: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RecoveryRecord:
    id: str
    tenant: str
    workspace: str
    profile_reference: str
    health_recheck: bool = True
    session_validation: bool = True
    browser_recovery_reference: str = ""
    proxy_replacement_reference: str = ""
    cooldown_seconds: int = 300
    checkpoint_reference: str = ""
    manual: bool = False
    maximum_attempts: int = 3
    attempts: int = 0
    outcome: str = "pending"
    unresolved_platform_condition: bool = False

    def validate(self) -> None:
        if not 0 <= self.cooldown_seconds <= 604_800:
            raise ValueError("Recovery cooldown must be bounded.")
        if not 1 <= self.maximum_attempts <= 10:
            raise ValueError("Maximum recovery attempts must be within [1, 10].")
