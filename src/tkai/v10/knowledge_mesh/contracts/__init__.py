"""Immutable metadata contracts for the V10 Sovereign Knowledge Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


class KnowledgeDomain(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    API = "api"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai_studio"
    DEPLOYMENT = "deployment"
    RELEASE = "release"
    DOCUMENTATION = "documentation"


class RelationshipType(str, Enum):
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    RELATED_TO = "related_to"
    DERIVED_FROM = "derived_from"
    COMPATIBLE_WITH = "compatible_with"
    GOVERNED_BY = "governed_by"
    VERIFIED_BY = "verified_by"
    TRUSTED_BY = "trusted_by"


@dataclass(frozen=True)
class KnowledgeProfile:
    profile_id: str
    subject_reference: str
    knowledge_domain: KnowledgeDomain
    concept_references: tuple[str, ...] = ()
    entity_references: tuple[str, ...] = ()
    relationship_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    provenance_references: tuple[str, ...] = ()
    lineage_references: tuple[str, ...] = ()
    version_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class DomainRecord:
    domain_id: str
    domain: KnowledgeDomain
    name: str
    description: str = ""
    version: str = "10.0.0"
    references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class KnowledgeConcept:
    concept_id: str
    name: str
    description: str
    category: str
    domain: KnowledgeDomain
    version: str = "10.0.0"
    status: str = "registered"
    tags: tuple[str, ...] = ()
    references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class KnowledgeEntity:
    entity_id: str
    entity_type: str
    attributes: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    references: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()
    version: str = "10.0.0"
    lifecycle: str = "registered"
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class KnowledgeRelationship:
    relationship_id: str
    source_reference: str
    target_reference: str
    relationship_type: RelationshipType
    version: str = "10.0.0"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    subject_reference: str
    source_reference: str
    evidence_reference: str
    verification_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class ProvenanceRecord:
    provenance_id: str
    subject_reference: str
    source_reference: str
    provenance_chain: tuple[str, ...] = ()
    verification_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class LineageRecord:
    lineage_id: str
    subject_reference: str
    lineage_chain: tuple[str, ...] = ()
    version_references: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class CompatibilityRecord:
    compatibility_id: str
    generation: str
    subject_reference: str
    version: str = "10.0.0"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


__all__ = (
    "CompatibilityRecord",
    "DomainRecord",
    "EvidenceRecord",
    "KnowledgeConcept",
    "KnowledgeDomain",
    "KnowledgeEntity",
    "KnowledgeProfile",
    "KnowledgeRelationship",
    "LineageRecord",
    "ProvenanceRecord",
    "RelationshipType",
)
