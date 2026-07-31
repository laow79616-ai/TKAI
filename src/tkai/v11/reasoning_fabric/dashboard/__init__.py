"""Read-only Reasoning Fabric dashboard projections."""

from typing import Protocol


class FabricProjection(Protocol):
    def overview(self) -> dict[str, object]: ...
    def projection(self, value: object) -> object: ...


DASHBOARD_SECTIONS = (
    "reasoning-fabric-overview",
    "profiles",
    "contexts",
    "claims",
    "premises",
    "evidence",
    "inferences",
    "assumptions",
    "constraints",
    "alternatives",
    "contradictions",
    "confidence",
    "uncertainty",
    "explanations",
    "evaluations",
    "relationships",
    "knowledge-graph",
    "compatibility",
    "governance",
    "trust",
    "integrity",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)


def dashboard_snapshot(fabric: FabricProjection) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": fabric.projection(fabric.overview()),
        "read_only": True,
        "actions": (),
        "mutation_enabled": False,
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
