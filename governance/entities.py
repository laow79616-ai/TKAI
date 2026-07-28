"""Domain entities for the Enterprise AI Governance Platform."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class GovernanceScopeType(str, Enum):
    TENANT = "tenant"
    ORGANIZATION = "organization"
    WORKSPACE = "workspace"
    APPLICATION = "application"
    AGENT = "agent"
    WORKFLOW = "workflow"
    MODEL = "model"
    PROMPT = "prompt"
    DATASET = "dataset"
    KNOWLEDGE_BASE = "knowledge_base"
    PLUGIN = "plugin"


class GovernanceStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"
    EXPIRED = "expired"


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class GovernanceScope:
    tenant: str
    workspace: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class GovernancePolicy:
    id: str
    tenant: str
    workspace: str
    name: str
    description: str
    scope_type: GovernanceScopeType
    scope_id: str
    owner: str
    version: str = "1.0.0"
    status: PolicyStatus = PolicyStatus.DRAFT
    rules: tuple[dict[str, Any], ...] = ()
    controls: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["scope_type"] = self.scope_type.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Risk:
    id: str
    tenant: str
    workspace: str
    category: str
    likelihood: Severity
    impact: Severity
    severity: Severity
    owner: str
    mitigation: str
    residual_risk: Severity
    status: GovernanceStatus = GovernanceStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        for name in ("likelihood", "impact", "severity", "residual_risk", "status"):
            value[name] = getattr(self, name).value
        return value


@dataclass(slots=True)
class ComplianceRecord:
    id: str
    tenant: str
    workspace: str
    framework: str
    control_mapping: dict[str, str] = field(default_factory=dict)
    evidence: tuple[str, ...] = ()
    assessment: str = ""
    finding: str = ""
    remediation: str = ""
    attestation: str = ""
    status: GovernanceStatus = GovernanceStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Approval:
    id: str
    tenant: str
    workspace: str
    resource_type: str
    resource_id: str
    requested_by: str
    approver: str | None = None
    status: GovernanceStatus = GovernanceStatus.PENDING
    reason: str = ""
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Control:
    id: str
    tenant: str
    workspace: str
    control_type: str
    name: str
    configuration: dict[str, Any] = field(default_factory=dict)
    status: GovernanceStatus = GovernanceStatus.ACTIVE

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class GovernedResource:
    id: str
    tenant: str
    workspace: str
    kind: str
    version: str
    owner: str
    approval_status: GovernanceStatus = GovernanceStatus.PENDING
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["approval_status"] = self.approval_status.value
        return value


@dataclass(slots=True)
class Incident:
    id: str
    tenant: str
    workspace: str
    severity: Severity
    source: str
    affected_resource: str
    owner: str
    status: GovernanceStatus = GovernanceStatus.ACTIVE
    timeline: tuple[dict[str, Any], ...] = ()
    containment: str = ""
    resolution: str = ""
    postmortem_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["severity"] = self.severity.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class PolicyException:
    id: str
    tenant: str
    workspace: str
    policy_id: str
    scope: str
    reason: str
    approver: str
    expiration: str
    compensating_control: str
    status: GovernanceStatus = GovernanceStatus.PENDING

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Evidence:
    id: str
    tenant: str
    workspace: str
    evidence_type: str
    reference: str
    resource_id: str
    checksum: str
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
