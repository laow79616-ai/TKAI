"""Read-only Operations Mesh dashboard projections."""

from tkai.v10.operations_mesh import SovereignOperationsMesh

DASHBOARD_SECTIONS = (
    "Operations Overview",
    "Contexts",
    "Operations",
    "Readiness",
    "Maintenance",
    "Capacity",
    "Availability",
    "Assessments",
    "Validation",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: SovereignOperationsMesh) -> dict[str, object]:
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
