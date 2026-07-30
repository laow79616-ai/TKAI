"""Read-only dashboard projections."""

from tkai.v9.compatibility_mesh.fabric import AdaptiveCompatibilityMesh

DASHBOARD_SECTIONS = (
    "Compatibility Mesh Overview",
    "Profiles",
    "Federation",
    "Components",
    "Versions",
    "Capabilities",
    "Configurations",
    "Schemas",
    "Storage",
    "Plugins",
    "Deployments",
    "Assessments",
    "Matrices",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: AdaptiveCompatibilityMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
