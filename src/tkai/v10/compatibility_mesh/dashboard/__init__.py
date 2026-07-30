"""Read-only dashboard projection."""

from tkai.v10.compatibility_mesh import SovereignCompatibilityMesh
from tkai.v10.compatibility_mesh.api import RESOURCES

DASHBOARD_SECTIONS = ("overview",) + RESOURCES


def dashboard_snapshot(mesh: SovereignCompatibilityMesh) -> dict[str, object]:
    return {
        "title": "Sovereign Compatibility Mesh Overview",
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }
