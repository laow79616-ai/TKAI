"""Reference-only relationship graph metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from tkai.v9.knowledge_mesh.contracts import (
    KnowledgeLifecycle,
    KnowledgeReference,
    immutable_metadata,
)


@dataclass(frozen=True)
class Relationship:
    source: str
    target: str
    kind: str
    relationship_id: str = ""
    direction: str = "directed"
    confidence: float = 0.0
    evidence_references: tuple[KnowledgeReference, ...] = ()
    validity_window: tuple[str, str] = ("", "")
    version: str = "1.0.0"
    integrity_status: str = "unverified"
    lifecycle: KnowledgeLifecycle = KnowledgeLifecycle.DRAFT
    audit_reference: KnowledgeReference | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.source or not self.target or not self.kind:
            raise ValueError("relationship source, target, and kind are required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


class RelationshipGraph:
    def __init__(self) -> None:
        self._relationships: list[Relationship] = []

    def add(self, relationship: Relationship) -> Relationship:
        self._relationships.append(relationship)
        return relationship

    def relationships(self) -> tuple[Relationship, ...]:
        return tuple(self._relationships)

    @staticmethod
    def executable() -> bool:
        return False


__all__ = ("Relationship", "RelationshipGraph")
