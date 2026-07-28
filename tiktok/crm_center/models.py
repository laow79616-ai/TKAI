"""Privacy-minimizing domain models for the TikTok CRM Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class CRMStatus(str, Enum):
    NEW = "new"
    QUALIFIED = "qualified"
    ACTIVE = "active"
    OPPORTUNITY = "opportunity"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ConsentStatus(str, Enum):
    UNKNOWN = "unknown"
    GRANTED = "granted"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True, slots=True)
class CRMScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:crm:read"})


SENSITIVE_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "cookie",
        "credential",
        "health",
        "biometric",
        "religion",
        "ethnicity",
        "political_opinion",
    }
)


def validate_metadata(value: dict[str, Any]) -> None:
    keys = {str(key).casefold().replace("-", "_") for key in value}
    if keys & SENSITIVE_KEYS:
        raise ValueError("Secrets and unnecessary sensitive attributes are prohibited.")
    if len(str(value)) > 16_384:
        raise ValueError("Metadata exceeds the bounded payload limit.")


def validate_reference(value: str, *, optional: bool = False) -> None:
    if optional and not value:
        return
    if (
        not value.startswith(
            ("ref://", "encrypted://", "tiktok-public://", "workspace://", "crm://")
        )
        or len(value) > 2048
    ):
        raise ValueError(
            "Only bounded opaque, encrypted, or public references are accepted."
        )


@dataclass(slots=True)
class CRMRecord:
    id: str
    display_name: str
    tenant: str
    workspace: str
    owner: str
    organization: str = ""
    contact_reference: str = ""
    lead_reference: str = ""
    priority: int = 50
    status: CRMStatus = CRMStatus.NEW
    stage: str = "new"
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
            raise ValueError("CRM identity and isolation scope are required.")
        if not 1 <= self.priority <= 100:
            raise ValueError("Priority must be within [1, 100].")
        validate_reference(self.contact_reference, optional=True)
        validate_reference(self.lead_reference, optional=True)
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Organization:
    id: str
    tenant: str
    workspace: str
    profile: str
    industry: str = ""
    country: str = ""
    region: str = ""
    tags: list[str] = field(default_factory=list)
    notes: str = ""
    relationship_status: str = "new"


@dataclass(slots=True)
class Contact:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    display_name: str
    role: str = ""
    preferred_language: str = ""
    timezone: str = ""
    public_tiktok_reference: str = ""
    consent_reference: str = ""
    relationship: str = ""


@dataclass(slots=True)
class Relationship:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    lead_reference: str = ""
    campaign_reference: str = ""
    creator_workspace_reference: str = ""
    business_workspace_reference: str = ""


@dataclass(slots=True)
class Opportunity:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    name: str
    stage: str
    value_reference: str = ""
    priority: int = 50
    probability: float = 0.0
    expected_timeline: str = ""
    approved: bool = False


@dataclass(slots=True)
class Activity:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    kind: str
    reference: str = ""
    note: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class FollowUp:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    proposal: str
    due_at: datetime
    owner: str
    consent_validated: bool
    approval_required: bool = True
    approved: bool = False
    status: str = "proposed"
    outcome: str = ""


@dataclass(slots=True)
class ConsentRecord:
    id: str
    crm_id: str
    tenant: str
    workspace: str
    status: ConsentStatus
    purpose: str
    timestamp: datetime
    withdrawal: str = ""
    suppression: bool = False


@dataclass(slots=True)
class AuditEvent:
    crm_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str = ""
    timestamp: datetime = field(default_factory=utcnow)
