"""Read-only dashboard projections for the V11 knowledge graph."""

from typing import Protocol


class GraphProjection(Protocol):
    def overview(self) -> dict[str, object]: ...

    def projection(self, value: object) -> object: ...


DASHBOARD_SECTIONS = (
    "graph-overview",
    "nodes",
    "edges",
    "relationships",
    "taxonomy",
    "ontology",
    "dependencies",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(graph: GraphProjection) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": graph.projection(graph.overview()),
        "read_only": True,
        "actions": (),
        "mutation_enabled": False,
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
