"""Immutable contracts for the advisory V8 Hyper Knowledge Fabric."""

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


class KnowledgeLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class KnowledgeScope:
    tenant: str = "default"
    workspace: str = "default"
    knowledge: str = "*"


@dataclass(frozen=True)
class KnowledgeReference:
    identifier: str
    version: str = ""
    uri: str = ""
    kind: str = "knowledge"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        generation = self.generation.lower()
        if generation not in {"", "v6", "v7", "v8"}:
            raise ValueError("reference generation must be V6, V7, or V8")
        object.__setattr__(self, "generation", generation)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class KnowledgeProfile:
    profile_id: str
    version: str
    owner: str
    framework_references: tuple[KnowledgeReference, ...] = ()
    knowledge_references: tuple[KnowledgeReference, ...] = ()
    ontology_references: tuple[KnowledgeReference, ...] = ()
    evidence_references: tuple[KnowledgeReference, ...] = ()
    relationship_references: tuple[KnowledgeReference, ...] = ()
    compatibility_references: tuple[KnowledgeReference, ...] = ()
    governance_references: tuple[KnowledgeReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: KnowledgeScope = KnowledgeScope()
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )


@dataclass(frozen=True)
class OntologyConcept:
    concept_id: str
    name: str
    categories: tuple[str, ...] = ()
    domains: tuple[str, ...] = ()
    relationship_types: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()
    parent_references: tuple[KnowledgeReference, ...] = ()
    version: str = "1.0.0"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.concept_id or not self.name or not self.version:
            raise ValueError("concept_id, name, and version are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class KnowledgeEntity:
    entity_id: str
    entity_type: str
    label: str = ""
    framework_references: tuple[KnowledgeReference, ...] = ()
    ontology_references: tuple[KnowledgeReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.entity_id or not self.entity_type:
            raise ValueError("entity_id and entity_type are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class KnowledgeRelationship:
    relationship_id: str
    source: KnowledgeReference
    target: KnowledgeReference
    relationship_type: str
    evidence_references: tuple[KnowledgeReference, ...] = ()
    semantics: Mapping[str, object] = field(default_factory=immutable_metadata)
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.relationship_id or not self.relationship_type:
            raise ValueError("relationship_id and relationship_type are required")
        object.__setattr__(self, "semantics", immutable_metadata(self.semantics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    evidence_reference: KnowledgeReference
    source_reference: KnowledgeReference
    origin: str
    timestamp: str
    integrity: str = "unknown"
    reliability: float = 0.0
    freshness: str = "unknown"
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not all((self.evidence_id, self.origin, self.timestamp)):
            raise ValueError("evidence_id, origin, and timestamp are required")
        if self.reliability < 0 or self.reliability > 1:
            raise ValueError("reliability must be between 0 and 1")
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class LineageRecord:
    lineage_id: str
    knowledge_reference: KnowledgeReference
    ancestor_references: tuple[KnowledgeReference, ...] = ()
    superseded_references: tuple[KnowledgeReference, ...] = ()
    derived_references: tuple[KnowledgeReference, ...] = ()
    compatibility_history: tuple[KnowledgeReference, ...] = ()
    evolution_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )

    def __post_init__(self) -> None:
        if not self.lineage_id:
            raise ValueError("lineage_id is required")
        object.__setattr__(
            self, "evolution_metadata", immutable_metadata(self.evolution_metadata)
        )


@dataclass(frozen=True)
class CompatibilityRecord:
    compatibility_id: str
    source: KnowledgeReference
    target: KnowledgeReference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.compatibility_id:
            raise ValueError("compatibility_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


Reference = KnowledgeReference

__all__ = (
    "CompatibilityRecord",
    "EvidenceRecord",
    "KnowledgeEntity",
    "KnowledgeLifecycle",
    "KnowledgeProfile",
    "KnowledgeReference",
    "KnowledgeRelationship",
    "KnowledgeScope",
    "LineageRecord",
    "OntologyConcept",
    "Reference",
    "immutable_metadata",
)
