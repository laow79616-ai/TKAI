"""Read-only Planning Mesh dashboard projection."""

from tkai.v9.planning_mesh.fabric import AdaptivePlanningMesh

DASHBOARD_SECTIONS = (
    "Planning Mesh Overview",
    "Objectives",
    "Constraints",
    "Scenarios",
    "Simulations",
    "Dependencies",
    "Resources",
    "Schedules",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: AdaptivePlanningMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
