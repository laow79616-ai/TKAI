"""Read-only dashboard projections."""

from tkai.v9.recovery_mesh.fabric import AdaptiveRecoveryMesh

DASHBOARD_SECTIONS = (
    "Recovery Mesh Overview",
    "Profiles",
    "Federation",
    "Incidents",
    "Recovery",
    "Rollback",
    "Snapshots",
    "Checkpoints",
    "Continuity",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: AdaptiveRecoveryMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
