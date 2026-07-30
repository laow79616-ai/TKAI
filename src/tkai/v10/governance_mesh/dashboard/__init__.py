"""Read-only dashboard projection for governance metadata."""

from tkai.v10.governance_mesh import SovereignGovernanceMesh

DASHBOARD_SECTIONS = (
    "overview",
    "profiles",
    "policies",
    "constraints",
    "reviews",
    "approvals",
    "risks",
    "compliance",
    "compatibility",
    "validation",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(mesh: SovereignGovernanceMesh) -> dict[str, object]:
    return {
        "title": "Governance Overview",
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
