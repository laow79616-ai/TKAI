"""Read-only dashboard projections."""

from tkai.v9.reasoning_mesh.fabric import AdaptiveReasoningMesh

DASHBOARD_SECTIONS = (
    "Reasoning Mesh Overview",
    "Profiles",
    "Federation",
    "Contexts",
    "Sources",
    "Knowledge",
    "Evidence",
    "Signals",
    "Observations",
    "Hypotheses",
    "Assumptions",
    "Constraints",
    "Reasoning",
    "Alternatives",
    "Comparisons",
    "Evaluations",
    "Confidence",
    "Recommendations",
    "Explainability",
    "Reviews",
    "Governance",
    "Policies",
    "Versions",
    "Compatibility",
    "History",
    "Analytics",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
    "Lifecycle",
)


def dashboard_snapshot(mesh: AdaptiveReasoningMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **mesh.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
