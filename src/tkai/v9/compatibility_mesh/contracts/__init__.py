"""Immutable advisory contracts for the V9 Adaptive Compatibility Mesh."""

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
        "proxy_credential",
        "secret",
        "session",
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


class CompatibilityLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    ASSESSING = "assessing"
    VALIDATING = "validating"
    COMPATIBLE = "compatible"
    CONDITIONALLY_COMPATIBLE = "conditionally_compatible"
    INCOMPATIBLE = "incompatible"
    UNDER_REVIEW = "under_review"
    APPROVED_REFERENCE = "approved_reference"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class CompatibilityScope:
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
    scope: CompatibilityScope = CompatibilityScope()
    source_generation: str = ""
    target_generation: str = "v9"
    component_references: tuple[Reference, ...] = ()
    capability_references: tuple[Reference, ...] = ()
    configuration_references: tuple[Reference, ...] = ()
    schema_references: tuple[Reference, ...] = ()
    storage_references: tuple[Reference, ...] = ()
    plugin_references: tuple[Reference, ...] = ()
    deployment_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    lifecycle: CompatibilityLifecycle = CompatibilityLifecycle.DRAFT
    tags: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        if not all(
            (self.profile_id, self.name, self.version, self.owner, self.namespace)
        ):
            raise ValueError(
                "profile identity, version, owner, and namespace are required"
            )
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class CompatibilityRecord:
    record_id: str
    category: str
    subject_reference: Reference
    target_reference: Reference | None = None
    status: str = "unknown"
    requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    scope: CompatibilityScope = CompatibilityScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))

    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False

    @property
    def mutates_configuration(self) -> bool:
        return False

    @property
    def mutates_schema(self) -> bool:
        return False

    @property
    def mutates_storage(self) -> bool:
        return False


@dataclass(frozen=True)
class Assessment:
    assessment_id: str
    category: str
    subject_reference: Reference
    target_reference: Reference
    status: str
    score: float
    factors: Mapping[str, float]
    weight_metadata: Mapping[str, float]
    requirements: tuple[str, ...] = ()
    gaps: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    explanation_summary: str = ""
    scope: CompatibilityScope = CompatibilityScope()
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
class Matrix:
    matrix_id: str
    source_generation: str
    target_generation: str
    entries: tuple[CompatibilityRecord, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: CompatibilityScope = CompatibilityScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    category: str
    subject_reference: Reference
    summary: str = ""
    requirements: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    scope: CompatibilityScope = CompatibilityScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Review:
    review_id: str
    artifact_reference: Reference
    reviewer: str
    status: str
    findings: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    scope: CompatibilityScope = CompatibilityScope()
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
    timestamp: datetime = field(default_factory=now)
    scope: CompatibilityScope = CompatibilityScope()
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)

    @property
    def authorizes_execution(self) -> bool:
        return False


CompatibilityMeshProfile = Profile
CompatibilityAssessment = Assessment
CompatibilityMatrix = Matrix
Component = Capability = Configuration = Schema = Storage = Plugin = Deployment = (
    Version
) = Migration = Upgrade = Rollback = GovernanceReference = CompatibilityRecord
MigrationAdvisory = UpgradeAdvisory = RollbackAdvisory = ConfigurationAdvisory = (
    SchemaAdvisory
) = StorageAdvisory = PluginAdvisory = DeploymentAdvisory = CompatibilityRecord

__all__ = (
    "Approval",
    "Assessment",
    "Capability",
    "CompatibilityAssessment",
    "CompatibilityLifecycle",
    "CompatibilityMatrix",
    "CompatibilityMeshProfile",
    "CompatibilityRecord",
    "CompatibilityScope",
    "Component",
    "Configuration",
    "ConfigurationAdvisory",
    "Deployment",
    "DeploymentAdvisory",
    "GovernanceReference",
    "Matrix",
    "Migration",
    "MigrationAdvisory",
    "Plugin",
    "PluginAdvisory",
    "Profile",
    "Recommendation",
    "Reference",
    "Review",
    "Rollback",
    "RollbackAdvisory",
    "Schema",
    "SchemaAdvisory",
    "Storage",
    "StorageAdvisory",
    "Upgrade",
    "UpgradeAdvisory",
    "Version",
    "VersionMetadata",
    "safe_metadata",
)
