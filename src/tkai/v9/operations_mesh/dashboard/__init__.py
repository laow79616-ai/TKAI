"""Read-only dashboard projections."""

from tkai.v9.operations_mesh.fabric import AdaptiveOperationsMesh

DASHBOARD_SECTIONS = (
    "Operations Mesh Overview",
    "Profiles",
    "Federation",
    "Operations",
    "Workflows",
    "Capabilities",
    "Services",
    "Resources",
    "Runtime",
    "Readiness",
    "Capacity",
    "Dependencies",
    "Constraints",
    "Risks",
    "Recovery",
    "Continuity",
    "Maintenance",
    "Pause",
    "Kill Switch",
    "Evaluations",
    "Recommendations",
    "Reviews",
    "Approvals",
    "Governance",
    "Compatibility",
    "History",
    "Analytics",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
    "Lifecycle",
)


def dashboard_snapshot(mesh: AdaptiveOperationsMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
