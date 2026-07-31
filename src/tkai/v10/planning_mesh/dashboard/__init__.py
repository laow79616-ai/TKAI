"""Read-only Planning Mesh dashboard projections."""

from tkai.v10.planning_mesh import SovereignPlanningMesh

DASHBOARD_SECTIONS = tuple(
    """planning_overview objectives milestones dependencies timelines readiness
validation health metrics audit""".split()
)


def dashboard_snapshot(mesh: SovereignPlanningMesh) -> dict[str, object]:
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
