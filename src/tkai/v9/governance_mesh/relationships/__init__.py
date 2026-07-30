"""Cross-framework governance relationships."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from tkai.v9.governance_mesh.contracts import immutable_metadata


@dataclass(frozen=True)
class GovernanceRelationship:
    source: str
    target: str
    kind: str
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.source or not self.target or not self.kind:
            raise ValueError("source, target, and kind are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


class RelationshipGraph:
    def __init__(self) -> None:
        self._items: list[GovernanceRelationship] = []

    def add(self, value: GovernanceRelationship) -> GovernanceRelationship:
        if value in self._items:
            raise ValueError("relationship already registered")
        self._items.append(value)
        return value

    def relationships(self) -> tuple[GovernanceRelationship, ...]:
        return tuple(self._items)


__all__ = ("GovernanceRelationship", "RelationshipGraph")
