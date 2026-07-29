"""Reference-only dependency and coordination graphs."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v8.hyper_coordination.contracts import CoordinationEdge, GraphKind


class CoordinationGraph:
    """Directed coordination graph with no execution edge type."""

    SUPPORTED_KINDS = frozenset(GraphKind)

    def __init__(self, edges: Iterable[CoordinationEdge] = ()) -> None:
        self._edges: list[CoordinationEdge] = []
        for edge in edges:
            self.add(edge)

    def add(self, edge: CoordinationEdge) -> CoordinationEdge:
        if edge.kind not in self.SUPPORTED_KINDS:
            raise ValueError("unsupported coordination graph kind")
        if edge not in self._edges:
            self._edges.append(edge)
        return edge

    def edges(self, kind: GraphKind | None = None) -> tuple[CoordinationEdge, ...]:
        selected = (
            self._edges
            if kind is None
            else [edge for edge in self._edges if edge.kind == kind]
        )
        return tuple(
            sorted(
                selected,
                key=lambda edge: (edge.kind.value, edge.source, edge.target),
            )
        )

    def adjacency(self, kind: GraphKind) -> dict[str, tuple[str, ...]]:
        result: dict[str, set[str]] = {}
        for edge in self.edges(kind):
            result.setdefault(edge.source, set()).add(edge.target)
            result.setdefault(edge.target, set())
        return {key: tuple(sorted(value)) for key, value in sorted(result.items())}

    def cycles(self, kind: GraphKind) -> tuple[tuple[str, ...], ...]:
        graph = self.adjacency(kind)
        found: set[tuple[str, ...]] = set()

        def visit(node: str, path: tuple[str, ...]) -> None:
            if node in path:
                start = path.index(node)
                found.add(path[start:] + (node,))
                return
            for target in graph.get(node, ()):
                visit(target, path + (node,))

        for node in graph:
            visit(node, ())
        return tuple(sorted(found))

    def snapshot(self) -> dict[str, object]:
        return {kind.value: self.adjacency(kind) for kind in GraphKind}


DependencyGraph = CoordinationGraph

__all__ = ("CoordinationGraph", "DependencyGraph")
