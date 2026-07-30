"""Immutable contracts for the advisory Hyper Recovery & Resilience Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


class RecoveryLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    ASSESSING = "assessing"
    PLANNING = "planning"
    VALIDATING = "validating"
    READY_FOR_REVIEW = "ready-for-review"
    UNDER_REVIEW = "under-review"
    APPROVED_REFERENCE = "approved-reference"
    DEGRADED = "degraded"
    RECOVERING_REFERENCE = "recovering-reference"
    RESTORED_REFERENCE = "restored-reference"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class FailureKind(str, Enum):
    CONFIGURATION = "configuration-failure"
    DEPENDENCY = "dependency-failure"
    CAPABILITY = "capability-failure"
    SERVICE = "service-failure"
    WORKFLOW = "workflow-failure"
    RESOURCE = "resource-failure"
    RUNTIME = "runtime-failure"
    STORAGE = "storage-failure"
    EVENT_DELIVERY = "event-delivery-failure"
    STATE_CONSISTENCY = "state-consistency-failure"
    SECURITY_POLICY = "security-policy-failure"
    GOVERNANCE = "governance-failure"
    COMPATIBILITY = "compatibility-failure"
    HEALTH_DEGRADATION = "health-degradation"
    CAPACITY_EXHAUSTION = "capacity-exhaustion-metadata"
    SCHEDULE = "schedule-failure-metadata"
    EXTERNAL_DEPENDENCY_REFERENCE = "external-dependency-reference-failure"


@dataclass(frozen=True)
class RecoveryScope:
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "default"
    profile: str = "default"


@dataclass(frozen=True)
class RecoveryReference:
    identifier: str
    kind: str = "metadata"
    version: str = ""
    generation: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        generation = self.generation.lower()
        if generation not in {"", "v6", "v7", "v8"}:
            raise ValueError("reference generation must be V6, V7, or V8")
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


Reference = RecoveryReference


@dataclass(frozen=True)
class RecoveryProfile:
    profile_id: str
    name: str
    version: str
    owner: str
    description: str = ""
    namespace: str = "default"
    tenant_reference: RecoveryReference | None = None
    workspace_reference: RecoveryReference | None = None
    scope: RecoveryScope = RecoveryScope()
    time_horizon: str = ""
    incident_references: tuple[RecoveryReference, ...] = ()
    failure_references: tuple[RecoveryReference, ...] = ()
    recovery_plan_references: tuple[RecoveryReference, ...] = ()
    rollback_references: tuple[RecoveryReference, ...] = ()
    snapshot_references: tuple[RecoveryReference, ...] = ()
    checkpoint_references: tuple[RecoveryReference, ...] = ()
    governance_references: tuple[RecoveryReference, ...] = ()
    compatibility_references: tuple[RecoveryReference, ...] = ()
    lifecycle: RecoveryLifecycle = RecoveryLifecycle.DRAFT
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    tags: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not all((self.profile_id, self.name, self.version, self.owner)):
            raise ValueError("profile_id, name, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def authorizes_execution(self) -> bool:
        return False


@dataclass(frozen=True)
class IncidentMetadata:
    incident_id: str
    incident_type: str
    source_reference: RecoveryReference
    subject_reference: RecoveryReference
    severity: str = "unknown"
    priority: str = "normal"
    started_at: str = ""
    detected_at: str = ""
    resolved_reference: RecoveryReference | None = None
    status: str = "recorded"
    impact_reference: RecoveryReference | None = None
    failure_references: tuple[RecoveryReference, ...] = ()
    evidence_references: tuple[RecoveryReference, ...] = ()
    governance_references: tuple[RecoveryReference, ...] = ()
    audit_reference: RecoveryReference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.incident_id or not self.incident_type:
            raise ValueError("incident_id and incident_type are required")
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class FailureClassification:
    failure_id: str
    kind: FailureKind
    subject_reference: RecoveryReference
    evidence_references: tuple[RecoveryReference, ...] = ()
    root_cause_claimed: bool = False
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    audit_reference: RecoveryReference | None = None

    def __post_init__(self) -> None:
        if not self.failure_id:
            raise ValueError("failure_id is required")
        if self.root_cause_claimed and not self.evidence_references:
            raise ValueError("root cause claims require supporting evidence")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between zero and one")


@dataclass(frozen=True)
class ImpactAssessment:
    impact_id: str
    affected_frameworks: tuple[RecoveryReference, ...] = ()
    affected_capabilities: tuple[RecoveryReference, ...] = ()
    affected_services: tuple[RecoveryReference, ...] = ()
    affected_workflows: tuple[RecoveryReference, ...] = ()
    affected_resources: tuple[RecoveryReference, ...] = ()
    affected_runtime_references: tuple[RecoveryReference, ...] = ()
    affected_tenants: tuple[RecoveryReference, ...] = ()
    affected_workspaces: tuple[RecoveryReference, ...] = ()
    availability_impact: str = "unknown"
    integrity_impact: str = "unknown"
    security_impact: str = "unknown"
    governance_impact: str = "unknown"
    compatibility_impact: str = "unknown"
    operational_impact: str = "unknown"
    estimated_duration: str = ""
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReadinessAssessment:
    readiness_id: str
    framework_readiness: float = 0
    capability_readiness: float = 0
    service_readiness: float = 0
    workflow_readiness: float = 0
    resource_readiness: float = 0
    runtime_readiness: float = 0
    snapshot_readiness: float = 0
    checkpoint_readiness: float = 0
    rollback_readiness: float = 0
    governance_readiness: float = 0
    security_readiness: float = 0
    compatibility_readiness: float = 0
    review_readiness: float = 0
    approval_readiness: float = 0
    limitations: tuple[str, ...] = ()

    @property
    def executes_recovery(self) -> bool:
        return False


@dataclass(frozen=True)
class ResilienceAssessment:
    resilience_id: str
    availability: float = 0
    dependency_redundancy_metadata: float = 0
    recovery_preparedness: float = 0
    snapshot_coverage: float = 0
    checkpoint_coverage: float = 0
    rollback_coverage: float = 0
    degraded_mode_coverage: float = 0
    governance_coverage: float = 0
    security_coverage: float = 0
    compatibility_coverage: float = 0
    operational_continuity: float = 0
    review_coverage: float = 0
    supporting_references: tuple[RecoveryReference, ...] = ()
    redundancy_claimed: bool = False
    limitations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.redundancy_claimed and not self.supporting_references:
            raise ValueError("redundancy claims require supporting references")


@dataclass(frozen=True)
class ContinuityMetadata:
    continuity_id: str
    continuity_plan_reference: RecoveryReference
    critical_capability_references: tuple[RecoveryReference, ...] = ()
    critical_service_references: tuple[RecoveryReference, ...] = ()
    critical_workflow_references: tuple[RecoveryReference, ...] = ()
    critical_resource_references: tuple[RecoveryReference, ...] = ()
    maximum_tolerable_downtime_metadata: str = ""
    recovery_time_objective_metadata: str = ""
    recovery_point_objective_metadata: str = ""
    degraded_operating_mode: RecoveryReference | None = None
    review_requirements: tuple[str, ...] = ()
    approval_requirements: tuple[str, ...] = ()
    governance_references: tuple[RecoveryReference, ...] = ()
    compatibility_references: tuple[RecoveryReference, ...] = ()


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_plan_id: str
    profile_reference: RecoveryReference
    incident_references: tuple[RecoveryReference, ...] = ()
    failure_references: tuple[RecoveryReference, ...] = ()
    objective_references: tuple[RecoveryReference, ...] = ()
    scope: RecoveryScope = RecoveryScope()
    preconditions: tuple[str, ...] = ()
    dependency_references: tuple[RecoveryReference, ...] = ()
    resource_references: tuple[RecoveryReference, ...] = ()
    snapshot_references: tuple[RecoveryReference, ...] = ()
    checkpoint_references: tuple[RecoveryReference, ...] = ()
    rollback_reference: RecoveryReference | None = None
    recovery_step_references: tuple[RecoveryReference, ...] = ()
    validation_references: tuple[RecoveryReference, ...] = ()
    governance_references: tuple[RecoveryReference, ...] = ()
    review_references: tuple[RecoveryReference, ...] = ()
    approval_references: tuple[RecoveryReference, ...] = ()
    confidence: float = 0
    risk_level: str = "unknown"
    status: str = "draft"
    version: str = "1"
    created_at: str = ""
    audit_reference: RecoveryReference | None = None

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class RecoveryStep:
    step_id: str
    recovery_plan_reference: RecoveryReference
    name: str
    description: str = ""
    step_type: str = "advisory"
    target_reference: RecoveryReference | None = None
    dependency_references: tuple[RecoveryReference, ...] = ()
    required_capability_references: tuple[RecoveryReference, ...] = ()
    resource_estimate: Mapping[str, object] = field(default_factory=immutable_metadata)
    duration_estimate: str = ""
    validation_requirement: str = ""
    governance_requirement: str = ""
    approval_requirement: str = ""
    rollback_reference: RecoveryReference | None = None
    sequence: int = 0
    status: str = "draft"
    audit_reference: RecoveryReference | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "resource_estimate", immutable_metadata(self.resource_estimate)
        )

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class RollbackPlan:
    rollback_plan_id: str
    target_reference: RecoveryReference
    baseline_reference: RecoveryReference
    snapshot_reference: RecoveryReference | None = None
    checkpoint_reference: RecoveryReference | None = None
    preconditions: tuple[str, ...] = ()
    dependency_references: tuple[RecoveryReference, ...] = ()
    resource_references: tuple[RecoveryReference, ...] = ()
    validation_references: tuple[RecoveryReference, ...] = ()
    risk_summary: str = ""
    governance_references: tuple[RecoveryReference, ...] = ()
    review_references: tuple[RecoveryReference, ...] = ()
    approval_references: tuple[RecoveryReference, ...] = ()
    status: str = "draft"
    version: str = "1"
    audit_reference: RecoveryReference | None = None

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class SnapshotMetadata:
    snapshot_id: str
    source_reference: RecoveryReference
    subject_reference: RecoveryReference
    version: str
    created_at: str
    payload_reference: RecoveryReference
    payload_hash: str
    integrity_status: str = "unknown"
    compatibility_status: str = "unknown"
    retention_reference: RecoveryReference | None = None
    validation_status: str = "unknown"
    audit_reference: RecoveryReference | None = None

    @property
    def restorable(self) -> bool:
        return False


@dataclass(frozen=True)
class CheckpointMetadata:
    checkpoint_id: str
    subject_reference: RecoveryReference
    state_reference: RecoveryReference
    configuration_reference: RecoveryReference | None = None
    resource_reference: RecoveryReference | None = None
    workflow_reference: RecoveryReference | None = None
    version: str = "1"
    created_at: str = ""
    integrity_status: str = "unknown"
    compatibility_status: str = "unknown"
    recovery_eligibility: str = "unassessed"
    audit_reference: RecoveryReference | None = None

    @property
    def restorable(self) -> bool:
        return False


@dataclass(frozen=True)
class AdvisoryArtifact:
    artifact_id: str
    artifact_type: str
    subject_reference: RecoveryReference | None = None
    references: tuple[RecoveryReference, ...] = ()
    status: str = "draft"
    version: str = "1"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit_reference: RecoveryReference | None = None

    def __post_init__(self) -> None:
        if not self.artifact_id or not self.artifact_type:
            raise ValueError("artifact_id and artifact_type are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    evaluation_type: str
    score: float
    factors: Mapping[str, float] = field(default_factory=dict)
    weight_metadata: Mapping[str, float] = field(default_factory=dict)
    supporting_references: tuple[RecoveryReference, ...] = ()
    limitations: tuple[str, ...] = ()
    explanation_summary: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("score must be between zero and one")
        object.__setattr__(self, "factors", immutable_metadata(self.factors))
        object.__setattr__(
            self, "weight_metadata", immutable_metadata(self.weight_metadata)
        )


@dataclass(frozen=True)
class Review:
    review_id: str
    reviewer: str
    scope: str
    findings: tuple[str, ...] = ()
    required_changes: tuple[str, ...] = ()
    advisory_recommendations: tuple[str, ...] = ()
    status: str = "pending"
    timestamp: str = ""
    audit_reference: RecoveryReference | None = None


@dataclass(frozen=True)
class Approval:
    approval_id: str
    artifact_reference: RecoveryReference
    artifact_version: str
    approval_scope: str
    approver: str
    decision: str
    conditions: tuple[str, ...] = ()
    expiry: str = ""
    timestamp: str = ""
    audit_reference: RecoveryReference | None = None

    @property
    def authorizes_execution(self) -> bool:
        return False


RestorationPlan = AdvisoryArtifact
DegradedMode = AdvisoryArtifact
DependencyAssessment = AdvisoryArtifact
ResourceAssessment = AdvisoryArtifact
CapacityAssessment = AdvisoryArtifact
ValidationResult = AdvisoryArtifact
Recommendation = AdvisoryArtifact
GovernanceMetadata = AdvisoryArtifact
CompatibilityMetadata = AdvisoryArtifact
VersionMetadata = AdvisoryArtifact
HealthMetadata = AdvisoryArtifact
MetricMetadata = AdvisoryArtifact


__all__ = tuple(name for name in globals() if not name.startswith("_"))
