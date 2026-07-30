"""Read-only dashboard projection for Hyper Decision."""

from tkai.v8.hyper_decision.fabric import HyperDecisionFabric

DASHBOARD_SECTIONS = (
    "Decision Overview",
    "Alternatives",
    "Comparisons",
    "Recommendations",
    "Reviews",
    "Approvals",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperDecisionFabric) -> dict[str, object]:
    return {
        "title": "TKAI V8 Hyper Decision Fabric",
        "sections": DASHBOARD_SECTIONS,
        "read_only": True,
        "data": fabric.snapshot(),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
