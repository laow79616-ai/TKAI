"""Mutable builder for deterministic immutable DependencyGraph snapshots."""

from __future__ import annotations

from .errors import ResolverGraphError
from .models import DependencyEdge, DependencyGraph, DependencyNode


class DependencyGraphBuilder:
    """Build a graph locally while rejecting duplicate edges and missing nodes."""

    def __init__(self) -> None:
        self._nodes: dict[object, DependencyNode] = {}
        self._edges: dict[tuple[object, object], DependencyEdge] = {}

    def add_node(self, node: DependencyNode) -> None:
        """Add or validate an identical node by its coordinate."""
        current = self._nodes.get(node.coordinate)
        if current is not None and current != node:
            raise ResolverGraphError("Dependency graph node coordinate is duplicated.")
        self._nodes[node.coordinate] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        """Add one edge after both explicit nodes have been supplied."""
        if edge.source not in self._nodes or edge.target not in self._nodes:
            raise ResolverGraphError("Dependency graph edges require existing nodes.")
        key = (edge.source, edge.target)
        if key in self._edges:
            raise ResolverGraphError("Dependency graph edge is duplicated.")
        self._edges[key] = edge

    def build(self) -> DependencyGraph:
        """Return a defensive immutable graph sorted by explicit coordinate keys."""
        return DependencyGraph(tuple(self._nodes.values()), tuple(self._edges.values()))
