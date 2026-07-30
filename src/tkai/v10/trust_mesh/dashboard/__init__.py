"""Read-only dashboard projection for trust metadata."""

from tkai.v10.trust_mesh import SovereignTrustMesh

DASHBOARD_SECTIONS = (
    "overview",
    "domains",
    "identities",
    "relationships",
    "integrity",
    "attestations",
    "scores",
    "compatibility",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(mesh: SovereignTrustMesh) -> dict[str, object]:
    return {
        "title": "Trust Mesh Overview",
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
