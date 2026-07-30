"""Read-only dashboard projection for integrity metadata."""

from tkai.v10.integrity_mesh import SovereignIntegrityMesh

DASHBOARD_SECTIONS = (
    "overview",
    "profiles",
    "subjects",
    "evidence",
    "verification",
    "dependencies",
    "compatibility",
    "releases",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(mesh: SovereignIntegrityMesh) -> dict[str, object]:
    return {
        "title": "Integrity Overview",
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
