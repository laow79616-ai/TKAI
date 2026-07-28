"""Privacy-minimizing domain models for the TikTok Lead Management Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LeadStatus(str, Enum):
    NEW = "new"
    IMPORTED = "imported"
    VALIDATED = "validated"
    DUPLICATE_REVIEW = "duplicate_review"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    ASSIGNED = "assigned"
    FOLLOW_UP_PLANNED = "follow_up_planned"
    ENGAGED = "engaged"
    CONVERTED = "converted"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LeadSource(str, Enum):
    MANUAL_ENTRY = "manual_entry"
    APPROVED_IMPORT = "approved_import"
    CAMPAIGN_REFERENCE = "campaign_reference"
    CONTENT_REFERENCE = "content_reference"
    INTERACTION_REFERENCE = "interaction_reference"
    LEAD_FORM_REFERENCE = "lead_form_reference"
    BUSINESS_WORKSPACE_REFERENCE = "business_workspace_reference"
    PUBLIC_PROFILE_REFERENCE = "public_profile_reference"
    EXTERNAL_CRM_REFERENCE = "external_crm_reference"


class ConsentStatus(str, Enum):
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"
    GRANTED = "granted"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    SUPPRESSED = "suppressed"


class HandoffTarget(str, Enum):
    BUSINESS_WORKSPACE = "business_workspace"
    CAMPAIGN_CENTER = "campaign_center"
    CREATOR_WORKSPACE = "creator_workspace"
    INTERACTION_CENTER = "interaction_center"
    WORKFLOW_CENTER = "workflow_center"
    AUTOMATION_ENGINE = "automation_engine"
    TASK_SCHEDULER = "task_scheduler"
    FUTURE_CRM = "future_crm_reference"


@dataclass(frozen=True, slots=True)
class LeadScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:leads:read"})


PROTECTED_FIELDS = frozenset(
    {
        "race",
        "ethnicity",
        "religion",
        "health",
        "disability",
        "sexual_orientation",
        "gender_identity",
        "political_opinion",
        "biometric",
        "genetic",
    }
)
SECRET_FIELDS = frozenset(
    {"password", "secret", "token", "cookie", "session", "proxy", "credential"}
)


def validate_metadata(value: dict[str, Any]) -> None:
    keys = {str(key).casefold().replace("-", "_") for key in value}
    if keys & PROTECTED_FIELDS:
        raise ValueError("Protected or sensitive attributes are prohibited.")
    if keys & SECRET_FIELDS:
        raise ValueError("Secrets are prohibited in lead metadata.")
    if len(str(value)) > 16_384:
        raise ValueError("Metadata exceeds the bounded payload limit.")


def validate_reference(value: str, *, optional: bool = False) -> None:
    if optional and not value:
        return
    allowed = (
        "ref://",
        "encrypted://",
        "tiktok-public://",
        "external://",
        "campaign://",
        "content://",
        "interaction://",
        "workspace://",
        "crm://",
    )
    if not value.startswith(allowed) or len(value) > 2048:
        raise ValueError("Only bounded opaque or public references are accepted.")


@dataclass(slots=True)
class Lead:
    id: str
    display_name: str
    tenant: str
    workspace: str
    owner: str
    source: LeadSource
    source_reference: str
    tiktok_public_reference: str = ""
    external_reference: str = ""
    status: LeadStatus = LeadStatus.NEW
    priority: int = 50
    stage: str = "new"
    consent_status: ConsentStatus = ConsentStatus.UNKNOWN
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.display_name.strip(),
                self.tenant,
                self.workspace,
                self.owner,
            )
        ):
            raise ValueError("Lead identity and isolation scope are required.")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be within [1, 100].")
        validate_reference(self.source_reference)
        validate_reference(self.tiktok_public_reference, optional=True)
        validate_reference(self.external_reference, optional=True)
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["source"] = self.source.value
        result["status"] = self.status.value
        result["consent_status"] = self.consent_status.value
        return result


@dataclass(slots=True)
class ConsentRecord:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    status: ConsentStatus
    source: str
    purpose: str
    timestamp: datetime
    expires_at: datetime | None = None
    withdrawal_reason: str = ""
    suppression: bool = False


@dataclass(slots=True)
class Qualification:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    qualified: bool
    reason: str
    business_relevance: float
    campaign_relevance: float
    geographic_relevance: float
    language_relevance: float
    evidence_references: list[str]
    manual_review: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class LeadScore:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    score: float
    priority: int
    confidence: float
    business_fit: float
    engagement_reference: float
    recency: float
    source_quality: float
    consent_state: float
    risk_flags: list[str]
    explanation: list[str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Assignment:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    owner: str
    operator: str
    reviewer: str
    rule_reference: str
    capacity: int
    priority: int
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Activity:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    kind: str
    reference: str
    note: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class FollowUp:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    plan: str
    due_at: datetime
    owner: str
    priority: int
    channel_reference: str
    template_reference: str
    approval_required: bool = True
    approved: bool = False
    status: str = "proposed"
    outcome: str = ""


@dataclass(slots=True)
class Handoff:
    id: str
    lead_id: str
    tenant: str
    workspace: str
    target: HandoffTarget
    reference: str
    approved: bool
    receipt_reference: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditEvent:
    lead_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
