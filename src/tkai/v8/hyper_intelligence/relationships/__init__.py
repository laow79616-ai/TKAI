"""Reference-only relationship graph metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from tkai.v8.hyper_intelligence.contracts import immutable_metadata


@dataclass(frozen=True)
class Relationship:
    source: str
    target: str
    kind: str
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.source or not self.target or not self.kind:
            raise ValueError("relationship source, target, and kind are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


class RelationshipGraph:
    def __init__(self) -> None:
        self._relationships: list[Relationship] = []

    def add(self, relationship: Relationship) -> Relationship:
        self._relationships.append(relationship)
        return relationship

    def relationships(self) -> tuple[Relationship, ...]:
        return tuple(self._relationships)


__all__ = ("Relationship", "RelationshipGraph")
