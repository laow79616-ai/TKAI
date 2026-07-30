"""Immutable reference-only records for the Adaptive Knowledge Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from tkai.v9.knowledge_mesh.contracts import (
    KnowledgeLifecycle,
    KnowledgeReference,
    KnowledgeScope,
    immutable_metadata,
)


@dataclass(frozen=True)
class VersionMetadata:
    version: str = "1.0.0"
    effective_date: str = ""
    superseded_by: KnowledgeReference | None = None
    change_reason: str = ""
    change_history: tuple[KnowledgeReference, ...] = ()
    deprecation_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )


@dataclass(frozen=True)
class Ontology:
    ontology_id: str
    name: str
    description: str = ""
    domain_references: tuple[KnowledgeReference, ...] = ()
    concept_references: tuple[KnowledgeReference, ...] = ()
    relationship_type_references: tuple[KnowledgeReference, ...] = ()
    constraint_references: tuple[KnowledgeReference, ...] = ()
    alias_references: tuple[KnowledgeReference, ...] = ()
    version: str = "1.0.0"
    compatibility_references: tuple[KnowledgeReference, ...] = ()
    governance_references: tuple[KnowledgeReference, ...] = ()
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT
    audit_reference: KnowledgeReference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: KnowledgeScope = KnowledgeScope()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class Taxonomy:
    taxonomy_id: str
    name: str
    domain_reference: KnowledgeReference
    category_references: tuple[KnowledgeReference, ...] = ()
    parent_references: tuple[KnowledgeReference, ...] = ()
    child_references: tuple[KnowledgeReference, ...] = ()
    alias_references: tuple[KnowledgeReference, ...] = ()
    version: str = "1.0.0"
    compatibility_references: tuple[KnowledgeReference, ...] = ()
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT
    audit_reference: KnowledgeReference | None = None
    scope: KnowledgeScope = KnowledgeScope()


@dataclass(frozen=True)
class Domain:
    domain_id: str
    name: str
    kind: str = "custom_bounded_domain"
    version: str = "1.0.0"
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: KnowledgeScope = KnowledgeScope()


@dataclass(frozen=True)
class Concept:
    concept_id: str
    name: str
    domain_reference: KnowledgeReference
    description: str = ""
    ontology_reference: KnowledgeReference | None = None
    taxonomy_reference: KnowledgeReference | None = None
    alias_references: tuple[KnowledgeReference, ...] = ()
    relationship_references: tuple[KnowledgeReference, ...] = ()
    knowledge_references: tuple[KnowledgeReference, ...] = ()
    evidence_references: tuple[KnowledgeReference, ...] = ()
    version: str = "1.0.0"
    confidence: float = 0.0
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT
    audit_reference: KnowledgeReference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: KnowledgeScope = KnowledgeScope()

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class Entity:
    entity_id: str
    entity_type: str
    canonical_name: str
    domain_reference: KnowledgeReference
    alias_references: tuple[KnowledgeReference, ...] = ()
    concept_references: tuple[KnowledgeReference, ...] = ()
    knowledge_references: tuple[KnowledgeReference, ...] = ()
    evidence_references: tuple[KnowledgeReference, ...] = ()
    relationship_references: tuple[KnowledgeReference, ...] = ()
    source_references: tuple[KnowledgeReference, ...] = ()
    version: str = "1.0.0"
    integrity_status: str = "unverified"
    confidence: float = 0.0
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT
    audit_reference: KnowledgeReference | None = None
    scope: KnowledgeScope = KnowledgeScope()


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    evidence_type: str
    source_reference: KnowledgeReference
    subject_reference: KnowledgeReference
    time_range: tuple[str, str] = ("", "")
    payload_reference: KnowledgeReference | None = None
    payload_hash: str = ""
    provenance_reference: KnowledgeReference | None = None
    reliability: float = 0.0
    relevance: float = 0.0
    freshness: float = 0.0
    integrity_status: str = "unverified"
    validation_status: str = "pending"
    version: str = "1.0.0"
    audit_reference: KnowledgeReference | None = None
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: KnowledgeScope = KnowledgeScope()

    def __post_init__(self) -> None:
        for name in ("reliability", "relevance", "freshness"):
            if not 0 <= getattr(self, name) <= 1:
                raise ValueError(f"{name} must be between 0 and 1")


@dataclass(frozen=True)
class Provenance:
    provenance_id: str
    origin_reference: KnowledgeReference
    source_type: str
    source_version: str = ""
    collection_time: str = ""
    transformation_references: tuple[KnowledgeReference, ...] = ()
    validation_references: tuple[KnowledgeReference, ...] = ()
    integrity_references: tuple[KnowledgeReference, ...] = ()
    custody_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    compatibility_references: tuple[KnowledgeReference, ...] = ()
    audit_reference: KnowledgeReference | None = None
    scope: KnowledgeScope = KnowledgeScope()


@dataclass(frozen=True)
class Lineage:
    lineage_id: str
    knowledge_ancestry: tuple[KnowledgeReference, ...] = ()
    evidence_ancestry: tuple[KnowledgeReference, ...] = ()
    derived_references: tuple[KnowledgeReference, ...] = ()
    superseded_references: tuple[KnowledgeReference, ...] = ()
    merged_references: tuple[KnowledgeReference, ...] = ()
    split_references: tuple[KnowledgeReference, ...] = ()
    transformation_references: tuple[KnowledgeReference, ...] = ()
    compatibility_history: tuple[KnowledgeReference, ...] = ()
    governance_history: tuple[KnowledgeReference, ...] = ()
    version_history: tuple[KnowledgeReference, ...] = ()
    scope: KnowledgeScope = KnowledgeScope()


@dataclass(frozen=True)
class QualityScore:
    score: float
    factors: Mapping[str, float]
    weight_metadata: Mapping[str, float]
    supporting_references: tuple[KnowledgeReference, ...] = ()
    limitations: tuple[str, ...] = ()
    explanation_summary: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("score must be between 0 and 1")
        object.__setattr__(self, "factors", immutable_metadata(self.factors))
        object.__setattr__(
            self, "weight_metadata", immutable_metadata(self.weight_metadata)
        )


@dataclass(frozen=True)
class Confidence:
    original_confidence: float
    evidence_adjusted_confidence: float
    source_adjusted_confidence: float
    freshness_adjusted_confidence: float
    provenance_adjusted_confidence: float
    lineage_adjusted_confidence: float
    compatibility_adjusted_confidence: float
    governance_adjusted_confidence: float
    calibrated_confidence: float
    confidence_explanation: str
    limitations: tuple[str, ...] = ()
    historical_accuracy_reference: KnowledgeReference | None = None

    def __post_init__(self) -> None:
        for value in (
            self.original_confidence,
            self.evidence_adjusted_confidence,
            self.source_adjusted_confidence,
            self.freshness_adjusted_confidence,
            self.provenance_adjusted_confidence,
            self.lineage_adjusted_confidence,
            self.compatibility_adjusted_confidence,
            self.governance_adjusted_confidence,
            self.calibrated_confidence,
        ):
            if not 0 <= value <= 1:
                raise ValueError("confidence values must be between 0 and 1")


__all__ = (
    "Concept",
    "Confidence",
    "Domain",
    "Entity",
    "Evidence",
    "Lineage",
    "Ontology",
    "Provenance",
    "QualityScore",
    "Taxonomy",
    "VersionMetadata",
)
