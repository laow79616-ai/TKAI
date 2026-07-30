"""Immutable advisory contracts for the V9 Adaptive Operations Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType

SECRET_PARTS = frozenset(
    {
        "access_token",
        "api_key",
        "authorization",
        "cookie",
        "password",
        "secret",
        "session",
        "proxy_credential",
    }
)


def safe_metadata(values: Mapping[str, object] | None = None) -> Mapping[str, object]:
    copied = dict(values or {})
    for key, value in copied.items():
        normalized = str(key).lower().replace("-", "_")
        if any(part in normalized for part in SECRET_PARTS):
            raise ValueError("secret-bearing metadata is prohibited")
        if isinstance(value, Mapping):
            safe_metadata(value)
    return MappingProxyType(copied)


def now() -> datetime:
    return datetime.now(timezone.utc)


class OperationsLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    FEDERATING = "federating"
    ASSESSING = "assessing"
    VALIDATING = "validating"
    READY = "ready"
    UNDER_REVIEW = "under_review"
    APPROVED_REFERENCE = "approved_reference"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    DEGRADED_REFERENCE = "degraded_reference"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class OperationsScope:
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "default"
    profile: str = "*"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class VersionMetadata:
    effective_date: datetime = field(default_factory=now)
    superseded_by: Reference | None = None
    change_reason: str = ""
    change_history: tuple[Reference, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "deprecation_metadata", safe_metadata(self.deprecation_metadata)
        )


@dataclass(frozen=True)
class Profile:
    profile_id: str
    name: str
    description: str
    version: str
    owner: str
    namespace: str
    tenant_reference: Reference
    workspace_reference: Reference
    scope: OperationsScope = OperationsScope()
    time_horizon: str = ""
    operation_references: tuple[Reference, ...] = ()
    workflow_references: tuple[Reference, ...] = ()
    capability_references: tuple[Reference, ...] = ()
    service_references: tuple[Reference, ...] = ()
    resource_references: tuple[Reference, ...] = ()
    runtime_references: tuple[Reference, ...] = ()
    readiness_references: tuple[Reference, ...] = ()
    recovery_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    lifecycle: OperationsLifecycle = OperationsLifecycle.DRAFT
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=safe_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    tags: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    created_at: datetime = field(default_factory=now)
    updated_at: datetime = field(default_factory=now)
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        if not all(
            (self.profile_id, self.name, self.version, self.owner, self.namespace)
        ):
            raise ValueError(
                "profile identity, version, owner, and namespace are required"
            )
        object.__setattr__(self, "metrics", safe_metadata(self.metrics))
        object.__setattr__(self, "safe_metadata", safe_metadata(self.safe_metadata))
        object.__setattr__(
            self, "audit", tuple(safe_metadata(item) for item in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class OperationReference:
    operation_id: str
    operation_type: str
    subject_reference: Reference
    objective_references: tuple[Reference, ...] = ()
    workflow_references: tuple[Reference, ...] = ()
    capability_references: tuple[Reference, ...] = ()
    service_references: tuple[Reference, ...] = ()
    resource_references: tuple[Reference, ...] = ()
    runtime_references: tuple[Reference, ...] = ()
    dependency_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    risk_references: tuple[Reference, ...] = ()
    recovery_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    status: str = "reference"
    version: str = "1.0.0"
    audit_reference: Reference | None = None
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Readiness:
    readiness_id: str
    subject_reference: Reference
    category: str
    statuses: Mapping[str, str] = field(default_factory=dict)
    overall_readiness: str = "unknown"
    evidence_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "statuses", safe_metadata(self.statuses))


@dataclass(frozen=True)
class Assessment:
    assessment_id: str
    category: str
    score: float
    status: str
    factors: Mapping[str, float]
    weight_metadata: Mapping[str, float]
    supporting_references: tuple[Reference, ...] = ()
    blocking_issues: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    explanation_summary: str = ""
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("score must be between 0 and 1")
        if not self.factors or not self.weight_metadata or not self.explanation_summary:
            raise ValueError(
                "explainable scores require factors, weights, and a summary"
            )
        if set(self.factors) != set(self.weight_metadata):
            raise ValueError("factor and weight keys must match")
        if abs(sum(self.weight_metadata.values()) - 1.0) > 0.001:
            raise ValueError("assessment weights must total 1")


@dataclass(frozen=True)
class CapacityAssessment:
    capacity_id: str
    category: str
    estimated_capacity: float
    estimated_demand: float
    estimated_utilization: float
    estimated_shortfall: float
    estimated_surplus: float
    forecast_reference: Reference | None = None
    constraint_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")

    @property
    def allocates_resources(self) -> bool:
        return False


@dataclass(frozen=True)
class Dependency:
    dependency_id: str
    category: str
    subject_reference: Reference
    required_references: tuple[Reference, ...] = ()
    status: str = "unknown"
    issues: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)


@dataclass(frozen=True)
class Constraint:
    constraint_id: str
    category: str
    summary: str
    references: tuple[Reference, ...] = ()
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)


@dataclass(frozen=True)
class Risk:
    risk_id: str
    category: str
    probability_metadata: Mapping[str, object]
    impact_metadata: Mapping[str, object]
    severity: str
    evidence_references: tuple[Reference, ...] = ()
    mitigation_references: tuple[Reference, ...] = ()
    recovery_references: tuple[Reference, ...] = ()
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "probability_metadata", safe_metadata(self.probability_metadata)
        )
        object.__setattr__(self, "impact_metadata", safe_metadata(self.impact_metadata))
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class AdvisoryRecord:
    record_id: str
    category: str
    subject_reference: Reference
    references: tuple[Reference, ...] = ()
    requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    category: str
    score: float
    factors: Mapping[str, float]
    weight_metadata: Mapping[str, float]
    supporting_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    explanation_summary: str = ""
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        Assessment(
            self.evaluation_id,
            self.category,
            self.score,
            "evaluated",
            self.factors,
            self.weight_metadata,
            self.supporting_references,
            (),
            self.limitations,
            self.explanation_summary,
            self.scope,
            self.version_metadata,
        )


@dataclass(frozen=True)
class Recommendation(AdvisoryRecord):
    @property
    def advisory(self) -> bool:
        return True


@dataclass(frozen=True)
class Review:
    review_id: str
    reviewer: str
    scope_summary: str
    findings: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()
    advisory_recommendations: tuple[Reference, ...] = ()
    status: str = "open"
    timestamp: datetime = field(default_factory=now)
    audit_reference: Reference | None = None
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)


@dataclass(frozen=True)
class Approval:
    approval_id: str
    artifact_reference: Reference
    artifact_version: str
    approval_scope: str
    approver: str
    decision: str
    conditions: tuple[str, ...] = ()
    expiry: datetime | None = None
    timestamp: datetime = field(default_factory=now)
    audit_reference: Reference | None = None
    scope: OperationsScope = OperationsScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    @property
    def authorizes_execution(self) -> bool:
        return False


OperationsMeshProfile = Profile
WorkflowReadiness = CapabilityReadiness = ServiceReadiness = ResourceReadiness = (
    RuntimeReadiness
) = Readiness
Recovery = Continuity = Maintenance = Pause = KillSwitch = GovernanceReference = (
    Compatibility
) = AdvisoryRecord

__all__ = (
    "AdvisoryRecord",
    "Approval",
    "Assessment",
    "CapacityAssessment",
    "Compatibility",
    "Constraint",
    "Continuity",
    "Dependency",
    "Evaluation",
    "GovernanceReference",
    "KillSwitch",
    "Maintenance",
    "OperationReference",
    "OperationsLifecycle",
    "OperationsMeshProfile",
    "OperationsScope",
    "Pause",
    "Profile",
    "Readiness",
    "Recommendation",
    "Recovery",
    "Reference",
    "ResourceReadiness",
    "Review",
    "Risk",
    "RuntimeReadiness",
    "ServiceReadiness",
    "VersionMetadata",
    "WorkflowReadiness",
    "CapabilityReadiness",
    "safe_metadata",
)
