"""Immutable domain models for the advisory TikTok Autonomous Planning Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "cookie",
        "session",
        "credential",
        "api_key",
        "proxy_password",
    }
)
MAX_METADATA_SIZE = 32_768


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    if SECRET_KEYS & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in autonomous planning records.")
    if len(str(value)) > MAX_METADATA_SIZE:
        raise ValueError("Metadata exceeds the bounded size.")


def validate_reference(value: str) -> None:
    if "://" not in value:
        raise ValueError("References must use opaque reference URIs.")


class PlanningStatus(str, Enum):
    DRAFT = "Draft"
    COLLECTING_INPUTS = "Collecting Inputs"
    GENERATING_CANDIDATES = "Generating Candidates"
    SIMULATING = "Simulating"
    VALIDATING = "Validating"
    READY_FOR_REVIEW = "Ready for Review"
    UNDER_REVIEW = "Under Review"
    APPROVED_REFERENCE = "Approved Reference"
    REJECTED = "Rejected"
    SUPERSEDED = "Superseded"
    ARCHIVED = "Archived"
    DELETED = "Deleted"


@dataclass(frozen=True, slots=True)
class PlanningContext:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:autonomous-planning:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(frozen=True, slots=True)
class PlanningProfile:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    planning_scope: str
    time_horizon_days: int
    planning_mode: str
    status: PlanningStatus = PlanningStatus.DRAFT
    version: int = 1
    tags: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PlanningArtifact:
    id: str
    tenant: str
    workspace: str
    kind: str
    name: str
    references: tuple[str, ...] = ()
    data: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    effective_date: datetime = field(default_factory=utcnow)
    superseded_by: str | None = None
    change_reason: str = "Initial version"


@dataclass(frozen=True, slots=True)
class Assumption:
    id: str
    tenant: str
    workspace: str
    description: str
    source: str
    evidence_reference: str
    confidence: float
    expiry: datetime
    validation_status: str
    risk_if_incorrect: str
    owner: str
    version: int = 1


@dataclass(frozen=True, slots=True)
class CandidatePlan:
    id: str
    tenant: str
    workspace: str
    profile_reference: str
    objective_references: tuple[str, ...]
    input_references: tuple[str, ...]
    constraint_references: tuple[str, ...]
    assumption_references: tuple[str, ...]
    planning_horizon_days: int
    priority: str
    status: PlanningStatus
    confidence: float
    risk_level: str
    explainability_summary: str
    version: int = 1
    created_at: datetime = field(default_factory=utcnow)
    advisory_only: bool = True
    execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class PlanStep:
    id: str
    tenant: str
    workspace: str
    plan_reference: str
    name: str
    description: str
    step_type: str
    objective_reference: str
    dependency_references: tuple[str, ...]
    required_capability_references: tuple[str, ...]
    resource_estimate: dict[str, float]
    duration_estimate_minutes: int
    schedule_window: str
    constraint_references: tuple[str, ...]
    risk_references: tuple[str, ...]
    validation_status: str
    approval_requirement: str
    handoff_reference: str | None
    sequence: int
    version: int = 1
    planning_artifact_only: bool = True
    execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class Evaluation:
    id: str
    tenant: str
    workspace: str
    plan_reference: str
    scores: dict[str, float]
    breakdown: dict[str, dict[str, float | str]]
    overall_plan_quality: float
    version: int = 1


@dataclass(frozen=True, slots=True)
class Approval:
    id: str
    tenant: str
    workspace: str
    plan_reference: str
    plan_version: int
    approval_scope: str
    approver: str
    decision: str
    conditions: tuple[str, ...]
    expiry: datetime | None
    timestamp: datetime
    audit_reference: str
    execution_authorized: bool = False


@dataclass(frozen=True, slots=True)
class ReferenceHandoff:
    id: str
    tenant: str
    workspace: str
    plan_reference: str
    destination: str
    reference: str
    created_at: datetime = field(default_factory=utcnow)
    reference_only: bool = True
    triggered: bool = False
