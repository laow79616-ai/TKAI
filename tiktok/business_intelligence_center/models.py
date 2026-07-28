"""Bounded, privacy-aware TikTok Business Intelligence domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceStatus(str, Enum):
    DRAFT = "draft"
    COLLECTING = "collecting"
    MODELING = "modeling"
    READY = "ready"
    REVIEW = "review"
    APPROVED = "approved"
    ARCHIVED = "archived"
    DELETED = "deleted"


class BusinessScope(str, Enum):
    BUSINESS_WORKSPACE = "business_workspace"
    LEAD_MANAGEMENT = "lead_management"
    CRM = "crm"
    CUSTOMER_JOURNEY = "customer_journey"
    CAMPAIGN = "campaign"
    CREATOR_WORKSPACE = "creator_workspace"
    CONTENT_PIPELINE = "content_pipeline"
    PUBLISHING = "publishing"
    WORKFLOW = "workflow"
    AUTOMATION = "automation"
    EXECUTION = "execution"
    OPERATIONS = "operations"
    RESOURCES = "resources"
    RISK = "risk"
    GROWTH = "growth"
    PERFORMANCE = "performance"
    PLATFORM = "platform"


class IntegrityStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    STALE = "stale"


@dataclass(frozen=True, slots=True)
class BIScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:business-intelligence:read"})


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
    {
        "password",
        "secret",
        "token",
        "cookie",
        "session",
        "proxy_credential",
        "credential",
    }
)


def validate_metadata(value: dict[str, Any]) -> None:
    keys = {str(key).casefold().replace("-", "_") for key in value}
    if keys & PROTECTED_FIELDS:
        raise ValueError("Protected attribute inference and storage are prohibited.")
    if keys & SECRET_FIELDS:
        raise ValueError("Secrets are prohibited in BI metadata.")
    if len(str(value)) > 16_384:
        raise ValueError("Metadata exceeds the bounded payload limit.")


def validate_reference(value: str, *, encrypted: bool = False) -> None:
    prefixes = ("encrypted://",) if encrypted else ("ref://", "encrypted://")
    if not value.startswith(prefixes) or len(value) > 2048:
        raise ValueError("Only bounded opaque references are accepted.")


@dataclass(slots=True)
class BIWorkspace:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    scope: BusinessScope
    status: WorkspaceStatus = WorkspaceStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (self.id, self.name.strip(), self.tenant, self.workspace, self.owner)
        ):
            raise ValueError("BI workspace identity and isolation scope are required.")
        validate_metadata(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["scope"] = self.scope.value
        result["status"] = self.status.value
        return result


@dataclass(slots=True)
class Dataset:
    id: str
    tenant: str
    workspace: str
    source_module: str
    source_reference: str
    schema_reference: str
    time_start: datetime
    time_end: datetime
    aggregation: str
    freshness_seconds: int
    version: int
    integrity_status: IntegrityStatus
    encrypted_reference: str
    consent_aware: bool = True
    purpose: str = "business_analytics"

    def validate(self) -> None:
        if self.time_start > self.time_end:
            raise ValueError("Dataset time range is invalid.")
        if self.freshness_seconds < 0:
            raise ValueError("Freshness cannot be negative.")
        validate_reference(self.source_reference)
        validate_reference(self.schema_reference)
        validate_reference(self.encrypted_reference, encrypted=True)


@dataclass(slots=True)
class SemanticModel:
    id: str
    tenant: str
    workspace: str
    business_entities: list[str]
    relationships: list[dict[str, str]]
    hierarchies: dict[str, list[str]]
    business_definitions: dict[str, str]
    version: int = 1


@dataclass(slots=True)
class Metric:
    id: str
    tenant: str
    workspace: str
    name: str
    description: str
    aggregation: str
    unit: str
    owner: str
    target_reference: str
    threshold_reference: str
    version: int = 1


@dataclass(slots=True)
class Query:
    id: str
    tenant: str
    workspace: str
    dataset: str
    kpis: list[str] = field(default_factory=list)
    metrics: list[str] = field(default_factory=list)
    dimensions: list[str] = field(default_factory=list)
    filters: dict[str, Any] = field(default_factory=dict)
    sorting: list[str] = field(default_factory=list)
    page: int = 1
    page_size: int = 100
    time_start: datetime = field(default_factory=utcnow)
    time_end: datetime = field(default_factory=utcnow)
    row_limit: int = 1000
    timeout_seconds: int = 10


@dataclass(slots=True)
class Insight:
    id: str
    tenant: str
    workspace: str
    summary: str
    finding: str
    affected_scope: str
    severity: str
    confidence: float
    evidence_references: list[str]
    comparison_reference: str = ""
    trend_reference: str = ""
    forecast_reference: str = ""
    recommended_review: str = ""


@dataclass(slots=True)
class AuditEvent:
    tenant: str
    workspace: str
    actor: str
    action: str
    reference: str
    timestamp: datetime = field(default_factory=utcnow)
