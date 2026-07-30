"""Read-only Decision Mesh dashboard projection."""

from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh

DASHBOARD_SECTIONS = (
    "Decision Mesh Overview",
    "Federation",
    "Decisions",
    "Alternatives",
    "Comparisons",
    "Recommendations",
    "Confidence",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(mesh: AdaptiveDecisionMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
