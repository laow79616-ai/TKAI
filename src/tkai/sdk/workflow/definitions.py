"""Compatibility-preserving declarative workflow definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum


class NodeKind(str, Enum):
    """Portable workflow node categories supported by the reference runtime."""

    TASK = "task"
    CONDITION = "condition"
    LOOP = "loop"
    RETRY = "retry"
    PARALLEL = "parallel"
    BRANCH = "branch"
    SEQUENCE = "sequence"
    END = "end"


@dataclass(frozen=True, slots=True)
class Node:
    """Immutable workflow node specification with explicit successors."""

    name: str
    kind: NodeKind = NodeKind.TASK
    handler: object | None = None
    successors: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class WorkflowDefinition:
    """Immutable SDK workflow graph; execution remains explicitly opt-in."""

    name: str
    nodes: tuple[Node, ...]
    entrypoint: str | None = None


class WorkflowBuilder:
    """Build validated declarations without selecting a runtime automatically."""

    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("Workflow name must not be empty.")
        self._name = name
        self._nodes: list[Node] = []

    def add(self, node: Node) -> WorkflowBuilder:
        """Add one uniquely named node while preserving declaration order."""
        if any(existing.name == node.name for existing in self._nodes):
            raise ValueError(f"Duplicate workflow node: {node.name}")
        self._nodes.append(node)
        return self

    def build(self, *, entrypoint: str | None = None) -> WorkflowDefinition:
        """Return an immutable declaration after shallow graph-name validation."""
        names = {node.name for node in self._nodes}
        if entrypoint is not None and entrypoint not in names:
            raise ValueError(f"Unknown workflow entrypoint: {entrypoint}")
        unknown = {
            item
            for node in self._nodes
            for item in node.successors
            if item not in names
        }
        if unknown:
            raise ValueError(f"Unknown workflow successors: {sorted(unknown)}")
        selected_entrypoint = entrypoint or (
            self._nodes[0].name if self._nodes else None
        )
        return WorkflowDefinition(self._name, tuple(self._nodes), selected_entrypoint)
