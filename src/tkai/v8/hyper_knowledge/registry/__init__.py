"""Deterministic registries for immutable knowledge metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from tkai.v8.hyper_knowledge.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    KnowledgeEntity,
    KnowledgeProfile,
    KnowledgeRelationship,
    LineageRecord,
    OntologyConcept,
)

T = TypeVar("T")


class KnowledgeRegistry(Generic[T]):
    def __init__(self, identifier: Callable[[T], str]) -> None:
        self._identifier = identifier
        self._records: dict[str, T] = {}

    def register(self, value: T) -> T:
        identifier = self._identifier(value)
        if identifier in self._records:
            raise ValueError(f"knowledge metadata already registered: {identifier}")
        self._records[identifier] = value
        return value

    def get(self, identifier: str) -> T:
        return self._records[identifier]

    def discover(self) -> tuple[T, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def __len__(self) -> int:
        return len(self._records)


class KnowledgeRegistryCatalog:
    def __init__(self) -> None:
        self.profiles = KnowledgeRegistry[KnowledgeProfile](
            lambda item: item.profile_id
        )
        self.ontology = KnowledgeRegistry[OntologyConcept](lambda item: item.concept_id)
        self.entities = KnowledgeRegistry[KnowledgeEntity](lambda item: item.entity_id)
        self.relationships = KnowledgeRegistry[KnowledgeRelationship](
            lambda item: item.relationship_id
        )
        self.evidence = KnowledgeRegistry[EvidenceRecord](lambda item: item.evidence_id)
        self.lineage = KnowledgeRegistry[LineageRecord](lambda item: item.lineage_id)
        self.compatibility = KnowledgeRegistry[CompatibilityRecord](
            lambda item: item.compatibility_id
        )


__all__ = ("KnowledgeRegistry", "KnowledgeRegistryCatalog")
