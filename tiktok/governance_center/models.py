"""Bounded domain models for TikTok autonomous governance."""

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
    ACTIVE = "active"
    MONITORING = "monitoring"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class GovernanceScope(str, Enum):
    STRATEGY = "strategy"
    MISSION = "mission"
    AUTONOMOUS_OPERATION = "autonomous_operation"
    PLANNING = "planning"
    DECISION = "decision"
    OPTIMIZATION = "optimization"
    AUTOMATION = "automation"
    EXECUTION = "execution"
    RECOVERY = "recovery"
    WORKFLOW = "workflow"
    SCHEDULER = "scheduler"
    RUNTIME = "runtime"
    RESOURCE = "resource"
    BROWSER_CLUSTER = "browser_cluster"
    DEVICE_CENTER = "device_center"
    PROXY_CENTER = "proxy_center"
    PUBLISHING = "publishing"
    COLLECTION = "collection"
    INTERACTION = "interaction"
    BUSINESS_WORKSPACE = "business_workspace"
    LEAD_MANAGEMENT = "lead_management"
    CRM = "crm"
    CUSTOMER_JOURNEY = "customer_journey"
    ANALYTICS = "analytics"
    PLATFORM = "platform"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    REVOKED = "revoked"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


CORE_PROHIBITIONS = frozenset(
    {
        "captcha_bypass",
        "restriction_circumvention",
        "security_bypass",
        "anti_detection_guarantee",
        "spam_automation",
        "unsolicited_bulk_messaging",
    }
)
SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "credential", "proxy_password"}
)


def validate_metadata(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {k.casefold() for k in value}:
        raise ValueError("Secrets are forbidden in governance metadata.")
    if len(str(value)) > 16384:
        raise ValueError("Governance metadata exceeds the bounded size.")


@dataclass(frozen=True, slots=True)
class AccessContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:governance-center:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class GovernanceProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    scopes: frozenset[GovernanceScope]
    priority: int = 3
    status: Lifecycle = Lifecycle.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not all(
            (self.id, self.name, self.tenant, self.workspace, self.owner, self.scopes)
        ):
            raise ValueError("Profile identity, ownership, and scope are required.")
        if not 1 <= self.priority <= 5 or self.version < 1:
            raise ValueError("Profile priority and version must be bounded.")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Policy:
    id: str
    profile_id: str
    policy_type: str
    tenant: str
    workspace: str
    scopes: frozenset[GovernanceScope]
    statement: str
    status: Lifecycle = Lifecycle.DRAFT
    version: int = 1
    effective_at: datetime | None = None
    expires_at: datetime | None = None
    superseded_by: str | None = None

    def validate(self) -> None:
        if (
            not all(
                (
                    self.id,
                    self.profile_id,
                    self.policy_type,
                    self.scopes,
                    self.statement,
                )
            )
            or self.version < 1
        ):
            raise ValueError("Policy must be bounded, versioned, and complete.")
        if (
            self.expires_at
            and self.effective_at
            and self.expires_at <= self.effective_at
        ):
            raise ValueError("Policy expiration must follow effective date.")


@dataclass(slots=True)
class PolicyRule:
    id: str
    policy_id: str
    tenant: str
    workspace: str
    scope: GovernanceScope
    condition: dict[str, Any]
    threshold: float
    time_window_seconds: int
    priority: int
    required_action: str
    required_approval: str | None = None
    cooldown_seconds: int = 0
    expires_at: datetime | None = None
    status: Lifecycle = Lifecycle.DRAFT
    version: int = 1

    def validate(self) -> None:
        if set(self.condition) != {"field", "operator", "value"} or self.condition[
            "operator"
        ] not in {"eq", "ne", "gt", "gte", "lt", "lte", "in"}:
            raise ValueError("Rule condition is not bounded.")
        if (
            "." in str(self.condition["field"])
            or self.time_window_seconds < 0
            or self.cooldown_seconds < 0
            or not 1 <= self.priority <= 5
        ):
            raise ValueError("Rule limits are invalid.")


@dataclass(slots=True)
class Control:
    id: str
    policy_id: str
    tenant: str
    workspace: str
    control_type: str
    scope: GovernanceScope
    limit: float | None = None
    status: Lifecycle = Lifecycle.DRAFT
    version: int = 1

    def validate(self) -> None:
        if not self.control_type or self.version < 1:
            raise ValueError("Control must be typed and versioned.")


@dataclass(slots=True)
class Approval:
    id: str
    resource_type: str
    resource_id: str
    tenant: str
    workspace: str
    approval_type: str
    reviewer: str | None = None
    notes: str = ""
    expires_at: datetime | None = None
    rejection_reason: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: datetime = field(default_factory=utcnow)
    decided_at: datetime | None = None

    def validate(self) -> None:
        validate_metadata({"notes_text": self.notes})


@dataclass(slots=True)
class Review:
    id: str
    target_id: str
    tenant: str
    workspace: str
    review_type: str
    reviewer: str
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    status: Lifecycle = Lifecycle.REVIEW
    created_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None

    def validate(self) -> None:
        if not all((self.id, self.target_id, self.review_type, self.reviewer)):
            raise ValueError("Review is incomplete.")


@dataclass(slots=True)
class ExceptionRequest:
    id: str
    policy_reference: str
    control_reference: str | None
    tenant: str
    workspace: str
    reason: str
    scope: GovernanceScope
    expires_at: datetime
    compensating_controls: tuple[str, ...]
    requested_prohibitions: frozenset[str] = frozenset()
    reviewer: str | None = None
    status: ApprovalStatus = ApprovalStatus.PENDING
    revoked_at: datetime | None = None

    def validate(self) -> None:
        if self.expires_at <= utcnow() or not self.compensating_controls:
            raise ValueError("Exception must be bounded and compensated.")
        if self.requested_prohibitions & CORE_PROHIBITIONS:
            raise PermissionError("Core safety prohibitions cannot be overridden.")


@dataclass(slots=True)
class Evidence:
    id: str
    evidence_type: str
    resource_id: str
    tenant: str
    workspace: str
    external_reference: str
    integrity_reference: str
    encrypted_reference: bool = True

    def validate(self) -> None:
        if (
            not self.external_reference
            or not self.integrity_reference
            or not self.encrypted_reference
        ):
            raise ValueError(
                "Encrypted evidence and integrity references are required."
            )


@dataclass(slots=True)
class ChangeRequest:
    id: str
    target_module: str
    tenant: str
    workspace: str
    current_version: str
    proposed_version: str
    change_type: str
    risk_level: RiskLevel
    impact: str
    preconditions: tuple[str, ...]
    approval_requirements: tuple[str, ...]
    backup_reference: str
    checkpoint_reference: str
    validation_plan: str
    rollback_plan: str
    status: ApprovalStatus = ApprovalStatus.PENDING

    def validate(self) -> None:
        if not all(
            (
                self.backup_reference,
                self.checkpoint_reference,
                self.validation_plan,
                self.rollback_plan,
            )
        ):
            raise ValueError(
                "Change requires backup, checkpoint, validation, and rollback."
            )


@dataclass(slots=True)
class RiskAssessment:
    id: str
    resource_id: str
    tenant: str
    workspace: str
    risk_profile_reference: str
    score: float
    level: RiskLevel
    factors: tuple[str, ...]
    affected_scope: GovernanceScope
    required_controls: tuple[str, ...]
    required_approval: str | None
    review_threshold: float
    escalation: str | None

    def validate(self) -> None:
        if not 0 <= self.score <= 100 or not 0 <= self.review_threshold <= 100:
            raise ValueError("Risk values must be within [0, 100].")


@dataclass(slots=True)
class AuditRecord:
    actor: str
    action: str
    resource: str
    scope: GovernanceScope
    tenant: str
    workspace: str
    before_state_reference: str | None
    after_state_reference: str | None
    policy_reference: str | None
    approval_reference: str | None
    reason: str
    correlation_id: str
    integrity_reference: str
    timestamp: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        validate_metadata({"actor_name": self.actor, "reason_text": self.reason})
        if not self.correlation_id or not self.integrity_reference:
            raise ValueError("Audit integrity is required.")
