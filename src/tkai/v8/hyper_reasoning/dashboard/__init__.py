"""Read-only dashboard projection for Hyper Reasoning."""

from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric

DASHBOARD_SECTIONS = (
    "Reasoning Overview",
    "Evidence",
    "Knowledge",
    "Confidence",
    "Recommendations",
    "Explainability",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperReasoningFabric) -> dict[str, object]:
    return {
        "title": "TKAI V8 Hyper Reasoning Fabric",
        "sections": DASHBOARD_SECTIONS,
        "read_only": True,
        "data": fabric.snapshot(),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
