"""Domain contracts for the Enterprise TikTok Business Workspace."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from re import fullmatch
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


FORBIDDEN_KEYS = {"password", "secret", "token", "cookie", "credential", "session"}
REFERENCE_PREFIXES = ("ref://", "kms://", "vault://")


class LifecycleStatus(str, Enum):
    DRAFT = "draft"
    PLANNING = "planning"
    ACTIVE = "active"
    REVIEW = "review"
    APPROVED = "approved"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class OperationKind(str, Enum):
    PLANNING = "planning"
    SCHEDULING = "scheduling"
    EXECUTION_COORDINATION = "execution_coordination"
    RESOURCE_COORDINATION = "resource_coordination"
    APPROVAL_COORDINATION = "approval_coordination"
    ANALYTICS_COORDINATION = "analytics_coordination"
    REVIEW_COORDINATION = "review_coordination"
    RECOVERY_COORDINATION = "recovery_coordination"


class CalendarKind(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CAMPAIGN = "campaign"
    PUBLISHING = "publishing"
    WORKFLOW = "workflow"
    REVIEW = "review"
    REMINDER = "reminder"


class BuiltinRole(str, Enum):
    OWNER = "owner"
    ADMINISTRATOR = "administrator"
    OPERATOR = "operator"
    REVIEWER = "reviewer"
    ANALYST = "analyst"
    VIEWER = "viewer"


class Permission(str, Enum):
    WORKSPACE_ACCESS = "workspace_access"
    PROJECT_ACCESS = "project_access"
    CAMPAIGN_ACCESS = "campaign_access"
    ANALYTICS_ACCESS = "analytics_access"
    APPROVAL_ACCESS = "approval_access"
    EXECUTION_PROPOSAL_ACCESS = "execution_proposal_access"
    HISTORY_ACCESS = "history_access"
    AUDIT_ACCESS = "audit_access"


class ApprovalKind(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    CAMPAIGN = "campaign"
    OPERATIONAL = "operational"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class CoordinationTarget(str, Enum):
    CREATOR_WORKSPACE = "creator_workspace"
    CAMPAIGN_CENTER = "campaign_center"
    CONTENT_PIPELINE = "content_pipeline"
    PUBLISHING_CENTER = "publishing_center"
    AUTOMATION_ENGINE = "automation_engine"
    EXECUTION_ENGINE = "execution_engine"
    RUNTIME_MANAGER = "runtime_manager"
    OPERATIONS_PLANNER = "operations_planner"
    DECISION_CENTER = "decision_center"
    CONTROL_TOWER = "control_tower"


@dataclass(frozen=True, slots=True)
class BusinessScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:business:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class BusinessWorkspace:
    id: str
    name: str
    description: str
    workspace: str
    owner: str
    tenant: str
    status: LifecycleStatus = LifecycleStatus.DRAFT
    priority: Priority = Priority.NORMAL
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        _validate_identity(self.id, self.name, self.workspace, self.owner, self.tenant)
        if self.version < 1:
            raise ValueError("Workspace version must be positive.")
        reject_secrets(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["priority"] = self.priority.value
        return value


@dataclass(slots=True)
class BusinessProject:
    id: str
    business_workspace_id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    campaign_reference: str = ""
    creator_workspace_reference: str = ""
    content_pipeline_reference: str = ""
    publishing_plan_reference: str = ""
    workflow_reference: str = ""
    automation_reference: str = ""
    execution_reference: str = ""
    priority: Priority = Priority.NORMAL
    schedule: datetime | None = None
    status: LifecycleStatus = LifecycleStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        _validate_identity(
            self.id,
            self.business_workspace_id,
            self.name,
            self.tenant,
            self.workspace,
            self.owner,
        )
        for reference in self.references().values():
            validate_reference(reference)
        reject_secrets(self.metadata)

    def references(self) -> dict[str, str]:
        return {
            "campaign": self.campaign_reference,
            "creator_workspace": self.creator_workspace_reference,
            "content_pipeline": self.content_pipeline_reference,
            "publishing_plan": self.publishing_plan_reference,
            "workflow": self.workflow_reference,
            "automation": self.automation_reference,
            "execution": self.execution_reference,
        }


@dataclass(slots=True)
class BusinessOperation:
    id: str
    project_id: str
    tenant: str
    workspace: str
    kind: OperationKind
    owner: str
    status: LifecycleStatus = LifecycleStatus.PLANNING
    schedule: datetime | None = None
    resource_references: list[str] = field(default_factory=list)
    approval_reference: str = ""
    coordination_reference: str = ""

    def validate(self) -> None:
        _validate_identity(
            self.id, self.project_id, self.tenant, self.workspace, self.owner
        )
        for reference in (
            *self.resource_references,
            self.approval_reference,
            self.coordination_reference,
        ):
            validate_reference(reference)


@dataclass(slots=True)
class CalendarEntry:
    id: str
    project_id: str
    tenant: str
    workspace: str
    kind: CalendarKind
    title: str
    starts_at: datetime
    timezone_name: str
    reminder_minutes: int = 0

    def validate(self) -> None:
        _validate_identity(
            self.id, self.project_id, self.tenant, self.workspace, self.title
        )
        if not fullmatch(r"[A-Za-z_+-]+(?:/[A-Za-z0-9_+-]+)*", self.timezone_name):
            raise ValueError("Timezone must be an IANA-style timezone name.")
        if self.reminder_minutes < 0:
            raise ValueError("Reminder minutes cannot be negative.")


@dataclass(slots=True)
class Role:
    id: str
    name: str
    tenant: str
    workspace: str
    permissions: frozenset[Permission]
    builtin: BuiltinRole | None = None

    def validate(self) -> None:
        _validate_identity(self.id, self.name, self.tenant, self.workspace)
        if not self.permissions:
            raise ValueError("Roles require at least one bounded permission.")


@dataclass(slots=True)
class Member:
    id: str
    business_workspace_id: str
    tenant: str
    workspace: str
    display_name: str
    role_id: str
    active: bool = True


@dataclass(slots=True)
class BusinessApproval:
    id: str
    resource_reference: str
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
        return self.status is ApprovalStatus.APPROVED and (
            self.expires_at is None or self.expires_at > utcnow()
        )


@dataclass(slots=True)
class CoordinationRequest:
    id: str
    project_id: str
    tenant: str
    workspace: str
    target: CoordinationTarget
    reference: str
    approval_reference: str = ""
    proposal_only: bool = True

    def validate(self) -> None:
        _validate_identity(self.id, self.project_id, self.tenant, self.workspace)
        validate_reference(self.reference)
        validate_reference(self.approval_reference)
        if not self.proposal_only:
            raise ValueError(
                "Business Workspace coordination must remain proposal-only."
            )


def _validate_identity(*values: str) -> None:
    if not all(values):
        raise ValueError("Identity and isolation scope fields are required.")


def validate_reference(reference: str) -> None:
    if reference and not reference.startswith(REFERENCE_PREFIXES):
        raise ValueError("References must be encrypted or opaque.")


def reject_secrets(value: dict[str, Any]) -> None:
    if FORBIDDEN_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are not permitted in Business Workspace metadata.")
