"""Read-only dashboard projections."""
# ruff: noqa: E501

from tkai.v10.reasoning_mesh import SovereignReasoningMesh

DASHBOARD_SECTIONS = tuple(
    """overview profiles contexts claims premises evidence inferences assumptions
constraints alternatives confidence uncertainty contradictions explanations assessments compatibility
governance integrity trust knowledge validation diagnostics health metrics audit lifecycle""".split()
)


def dashboard_snapshot(mesh: SovereignReasoningMesh) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
