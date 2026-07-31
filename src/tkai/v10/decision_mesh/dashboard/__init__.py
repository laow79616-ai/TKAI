"""Read-only Decision Mesh dashboard projections."""

from tkai.v10.decision_mesh import SovereignDecisionMesh

DASHBOARD_SECTIONS = tuple(
    """decision_overview contexts options evaluations criteria tradeoffs recommendations
confidence validation health metrics audit""".split()
)


def dashboard_snapshot(mesh: SovereignDecisionMesh) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
