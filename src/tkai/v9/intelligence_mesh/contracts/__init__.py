"""Immutable contracts for the metadata-only Adaptive Intelligence Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    """Copy metadata into a read-only mapping."""

    return MappingProxyType(dict(values or {}))


class IntelligenceLifecycle(str, Enum):
    """Lifecycle of intelligence metadata, never of runtime execution."""

    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATED = "validated"
    PUBLISHED = "published"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class IntelligenceScope:
    """Tenant, workspace, and knowledge isolation coordinates."""

    tenant: str = "default"
    workspace: str = "default"
    knowledge_namespace: str = "default"


@dataclass(frozen=True)
class IntelligenceReference:
    """A governed reference to metadata owned by another component."""

    identifier: str
    version: str = ""
    uri: str = ""
    kind: str = "metadata"
    generation: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    relationship: str = ""
    referenced_version: str = ""

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class FederationProfile:
    """Complete cross-version intelligence metadata profile."""

    profile_id: str
    version: str
    owner: str
    framework_references: tuple[IntelligenceReference, ...] = ()
    ai_center_references: tuple[IntelligenceReference, ...] = ()
    knowledge_references: tuple[IntelligenceReference, ...] = ()
    evidence_references: tuple[IntelligenceReference, ...] = ()
    signal_references: tuple[IntelligenceReference, ...] = ()
    context_references: tuple[IntelligenceReference, ...] = ()
    compatibility_references: tuple[IntelligenceReference, ...] = ()
    governance_references: tuple[IntelligenceReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()
    lifecycle: IntelligenceLifecycle = IntelligenceLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        """Intelligence metadata can never authorize execution."""

        return False


@dataclass(frozen=True)
class KnowledgeRecord:
    """Reference-only knowledge graph node metadata."""

    knowledge_id: str
    label: str
    kind: str
    evidence_references: tuple[IntelligenceReference, ...] = ()
    context_references: tuple[IntelligenceReference, ...] = ()
    relationship_references: tuple[IntelligenceReference, ...] = ()
    version: str = "1.0.0"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        if not self.knowledge_id or not self.label:
            raise ValueError("knowledge_id and label are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class EvidenceRecord:
    """Evidence linkage and provenance metadata, never evidence payload content."""

    evidence_id: str
    source_reference: IntelligenceReference
    knowledge_references: tuple[IntelligenceReference, ...] = ()
    provenance: Mapping[str, object] = field(default_factory=immutable_metadata)
    reliability: float | None = None
    freshness: str = "unknown"
    integrity: str = "unverified"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if self.reliability is not None and not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        object.__setattr__(self, "provenance", immutable_metadata(self.provenance))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class SignalRecord:
    """Observed signal metadata without runtime or TikTok action semantics."""

    signal_id: str
    signal_type: str
    source_reference: IntelligenceReference
    evidence_references: tuple[IntelligenceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        if not self.signal_id or not self.signal_type:
            raise ValueError("signal_id and signal_type are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ReasoningSummary:
    """Safe reasoning summary with references; hidden reasoning is prohibited."""

    summary_id: str
    summary: str
    evidence_references: tuple[IntelligenceReference, ...] = ()
    confidence: float | None = None
    evaluation_references: tuple[IntelligenceReference, ...] = ()
    explanation_references: tuple[IntelligenceReference, ...] = ()
    confidence_references: tuple[IntelligenceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        if not self.summary_id or not self.summary:
            raise ValueError("summary_id and summary are required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        forbidden = {"chain_of_thought", "hidden_reasoning", "internal_reasoning"}
        if forbidden.intersection(key.lower() for key in self.metadata):
            raise ValueError("hidden reasoning metadata is prohibited")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class Recommendation:
    """Advisory, reference-only recommendation."""

    recommendation_id: str
    summary: str
    evidence_references: tuple[IntelligenceReference, ...] = ()
    reasoning_reference: IntelligenceReference | None = None
    confidence: float | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        if not self.recommendation_id or not self.summary:
            raise ValueError("recommendation_id and summary are required")
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def advisory(self) -> bool:
        return True

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class CompatibilityRecord:
    """Cross-version compatibility metadata."""

    compatibility_id: str
    source: IntelligenceReference
    target: IntelligenceReference
    status: str = "compatible"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        generations = {self.source.generation, self.target.generation}
        if not generations.issubset({"", "v6", "v7", "v8", "v9"}):
            raise ValueError("compatibility generations must be V6, V7, V8, or V9")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ConfidenceRecord:
    """Calibrated confidence metadata with no model-internal reasoning."""

    confidence_id: str
    value: float
    calibration: Mapping[str, object] = field(default_factory=immutable_metadata)
    evidence_coverage: float = 0.0
    reliability: float = 0.0
    limitations: tuple[str, ...] = ()
    version_history: tuple[str, ...] = ()
    scope: IntelligenceScope = IntelligenceScope()

    def __post_init__(self) -> None:
        for name, value in (
            ("value", self.value),
            ("evidence_coverage", self.evidence_coverage),
            ("reliability", self.reliability),
        ):
            if not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        object.__setattr__(self, "calibration", immutable_metadata(self.calibration))


Reference = IntelligenceReference
IntelligenceProfile = FederationProfile

__all__ = (
    "CompatibilityRecord",
    "ConfidenceRecord",
    "EvidenceRecord",
    "FederationProfile",
    "IntelligenceLifecycle",
    "IntelligenceProfile",
    "IntelligenceReference",
    "IntelligenceScope",
    "KnowledgeRecord",
    "ReasoningSummary",
    "Recommendation",
    "Reference",
    "SignalRecord",
    "immutable_metadata",
)
