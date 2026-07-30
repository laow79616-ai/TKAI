"""Bounded, reference-only topology and dependency validation."""

from __future__ import annotations

from collections import defaultdict

from tkai.v10.contracts import Reference, TopologyEdge

EDGE_KINDS = frozenset(
    {
        "dependency",
        "compatibility",
        "governance",
        "security",
        "trust",
        "integrity",
        "attestation",
        "configuration",
        "event",
        "state",
        "runtime",
        "health",
        "observability",
    }
)


class MetadataTopology:
    def __init__(self, *, max_nodes: int = 2_000, max_edges: int = 10_000) -> None:
        self.max_nodes, self.max_edges = max_nodes, max_edges
        self._nodes: dict[str, Reference] = {}
        self._edges: list[TopologyEdge] = []

    def add_node(self, node: Reference) -> Reference:
        if node.identifier not in self._nodes and len(self._nodes) >= self.max_nodes:
            raise ValueError("bounded node count exceeded")
        self._nodes[node.identifier] = node
        return node

    def add_edge(self, edge: TopologyEdge) -> TopologyEdge:
        if edge.kind not in EDGE_KINDS:
            raise ValueError(f"unsupported edge kind: {edge.kind}")
        if len(self._edges) >= self.max_edges:
            raise ValueError("bounded edge count exceeded")
        self._edges.append(edge)
        return edge

    def nodes(self) -> tuple[Reference, ...]:
        return tuple(sorted(self._nodes.values(), key=lambda item: item.identifier))

    def edges(self) -> tuple[TopologyEdge, ...]:
        return tuple(
            sorted(self._edges, key=lambda item: (item.source, item.target, item.kind))
        )

    def issues(self) -> tuple[dict[str, str], ...]:
        issues: list[dict[str, str]] = []
        graph: dict[str, list[str]] = defaultdict(list)
        for edge in self._edges:
            if edge.source not in self._nodes or edge.target not in self._nodes:
                issues.append(
                    {
                        "code": "missing-dependency",
                        "source": edge.source,
                        "target": edge.target,
                    }
                )
            if edge.kind == "dependency":
                graph[edge.source].append(edge.target)
                target = self._nodes.get(edge.target)
                if (
                    target
                    and edge.required_version
                    and target.version != edge.required_version
                ):
                    issues.append(
                        {
                            "code": "version-conflict",
                            "source": edge.source,
                            "target": edge.target,
                        }
                    )
                if target and not target.integrity_reference:
                    issues.append(
                        {
                            "code": "integrity-gap",
                            "source": edge.source,
                            "target": edge.target,
                        }
                    )
                if target and not target.attestation_reference:
                    issues.append(
                        {
                            "code": "attestation-gap",
                            "source": edge.source,
                            "target": edge.target,
                        }
                    )
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(node: str) -> None:
            if node in visiting:
                issues.append({"code": "circular-dependency", "node": node})
                return
            if node in visited:
                return
            visiting.add(node)
            for target in graph[node]:
                visit(target)
            visiting.remove(node)
            visited.add(node)

        for node in sorted(self._nodes):
            visit(node)
        return tuple(sorted(issues, key=lambda item: tuple(sorted(item.items()))))


__all__ = ("EDGE_KINDS", "MetadataTopology")
