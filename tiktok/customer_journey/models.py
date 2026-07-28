"""Domain models for the Enterprise TikTok Customer Journey Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class JourneyStatus(str, Enum):
    NEW = "new"
    AWARENESS = "awareness"
    INTEREST = "interest"
    CONSIDERATION = "consideration"
    QUALIFIED = "qualified"
    OPPORTUNITY = "opportunity"
    CONVERTED = "converted"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class JourneyStage(str, Enum):
    AWARENESS = "awareness"
    INTEREST = "interest"
    ENGAGEMENT = "engagement"
    QUALIFICATION = "qualification"
    OPPORTUNITY = "opportunity"
    CONVERSION = "conversion"
    RETENTION = "retention"
    REACTIVATION = "reactivation"
    CUSTOM = "custom_bounded_stage"


class MilestoneState(str, Enum):
    REACHED = "reached"
    PENDING = "pending"
    SKIPPED = "skipped"
    MANUAL_OVERRIDE = "manual_override"


class HandoffTarget(str, Enum):
    CRM_CENTER = "crm_center"
    LEAD_CENTER = "lead_center"
    CAMPAIGN_CENTER = "campaign_center"
    CREATOR_WORKSPACE = "creator_workspace"
    WORKFLOW_CENTER = "workflow_center"
    AUTOMATION_ENGINE = "automation_engine"


class ConsentState(str, Enum):
    UNKNOWN = "unknown"
    NOT_REQUIRED = "not_required"
    GRANTED = "granted"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True, slots=True)
class JourneyScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:customer-journeys:read"})


SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "session", "proxy", "credential"}
)


def validate_metadata(value: dict[str, Any]) -> None:
    keys = {str(key).casefold().replace("-", "_") for key in value}
    if keys & SECRET_KEYS:
        raise ValueError("Secrets are prohibited in journey metadata.")
    if len(str(value)) > 16_384:
        raise ValueError("Metadata exceeds the bounded payload limit.")


def validate_reference(value: str, *, optional: bool = False) -> None:
    if optional and not value:
        return
    if not value.startswith(("ref://", "encrypted://")) or len(value) > 2048:
        raise ValueError("Only bounded opaque or encrypted references are accepted.")


@dataclass(slots=True)
class Journey:
    id: str
    name: str
    tenant: str
    workspace: str
    owner: str
    lead_reference: str
    crm_reference: str
    campaign_reference: str = ""
    stage: JourneyStage = JourneyStage.AWARENESS
    status: JourneyStatus = JourneyStatus.NEW
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        identity = (self.id, self.name.strip(), self.tenant, self.workspace, self.owner)
        if not all(identity):
            raise ValueError("Journey identity and isolation scope are required.")
        for value in (
            self.lead_reference,
            self.crm_reference,
            self.campaign_reference,
        ):
            validate_reference(value, optional=not value)
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["stage"] = self.stage.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Touchpoint:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    kind: str
    reference: str
    occurred_at: datetime
    timeline_note: str = ""


@dataclass(slots=True)
class Milestone:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    name: str
    state: MilestoneState
    timestamp: datetime
    reason: str = ""


@dataclass(slots=True)
class Segment:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    campaign: str = ""
    region: str = ""
    language: str = ""
    product: str = ""
    priority: int = 50
    consent_state: ConsentState = ConsentState.UNKNOWN
    status: str = "active"


@dataclass(slots=True)
class Recommendation:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    suggested_next_step: str
    confidence: float
    evidence: list[str]
    suggested_campaign: str = ""
    suggested_content: str = ""
    suggested_workflow: str = ""
    suggested_follow_up_proposal: str = ""
    advisory_only: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class Conversion:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    event: str
    conversion_reference: str
    timestamp: datetime
    attribution_reference: str
    outcome: str


@dataclass(slots=True)
class Handoff:
    id: str
    journey_id: str
    tenant: str
    workspace: str
    target: HandoffTarget
    reference: str
    approved: bool
    receipt_reference: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditEvent:
    journey_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
