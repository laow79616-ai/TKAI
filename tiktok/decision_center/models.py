"""Domain contracts for the TikTok AI Intelligent Decision Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DecisionStatus(str, Enum):
    DRAFT = "draft"
    ANALYZING = "analyzing"
    PROPOSED = "proposed"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    DELETED = "deleted"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


DECISION_INPUTS = (
    "account_state",
    "browser_cluster_state",
    "device_state",
    "proxy_state",
    "runtime_state",
    "workflow_state",
    "automation_state",
    "execution_state",
    "recovery_state",
    "risk_state",
    "analytics_kpis",
    "resource_utilization",
)

DASHBOARD_SECTIONS = (
    "Overview",
    "Decisions",
    "Recommendations",
    "Evidence",
    "Approvals",
    "History",
    "Analytics",
)


def validate_safe_mapping(value: dict[str, Any]) -> None:
    forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
    if forbidden & {key.casefold() for key in value}:
        raise ValueError("Secrets are forbidden in decision metadata.")


@dataclass(frozen=True, slots=True)
class DecisionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:decision:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Decision:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    priority: int
    status: DecisionStatus = DecisionStatus.DRAFT
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (
                self.id,
                self.name,
                self.description,
                self.tenant,
                self.workspace,
                self.owner,
            )
        ):
            raise ValueError("Decision identity, scope, and owner are required.")
        if not 1 <= self.priority <= 5:
            raise ValueError("Decision priority must be within [1, 5].")
        validate_safe_mapping(self.metadata)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class DecisionContext:
    decision_id: str
    tenant: str
    workspace: str
    inputs: dict[str, dict[str, Any]]
    captured_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DecisionConstraint:
    name: str
    threshold: float
    actual: float
    passed: bool
    detail: str


@dataclass(slots=True)
class DecisionEvaluation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    objective_score: float
    risk_score: float
    capacity_score: float
    resource_score: float
    confidence_score: float
    constraints: list[DecisionConstraint]
    evidence_references: list[str]
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DecisionRecommendation:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    suggested_action: str
    suggested_schedule: str
    suggested_resources: list[str]
    suggested_workflow: str
    suggested_recovery: str
    expected_outcome: str
    confidence: float
    risk_level: RiskLevel
    advisory: bool = True
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DecisionApproval:
    id: str
    decision_id: str
    recommendation_id: str
    tenant: str
    workspace: str
    reviewer: str
    approved: bool
    approval_notes: str
    expires_at: datetime
    execution_handoff_reference: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class EvidenceRecord:
    id: str
    decision_id: str
    tenant: str
    workspace: str
    kind: str
    reference: str
    summary: str
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class DecisionHistory:
    decision_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    detail: str
    timestamp: datetime = field(default_factory=utcnow)
