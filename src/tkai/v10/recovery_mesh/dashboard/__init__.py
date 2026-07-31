"""Read-only Sovereign Recovery Mesh dashboard projections."""

from tkai.v10.recovery_mesh import SovereignRecoveryMesh

DASHBOARD_SECTIONS = (
    "Recovery Overview",
    "Profiles",
    "Strategies",
    "Plans",
    "Readiness",
    "Validation",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: SovereignRecoveryMesh) -> dict[str, object]:
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
