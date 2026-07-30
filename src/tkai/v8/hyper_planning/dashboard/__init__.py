"""Read-only dashboard projection for Hyper Planning."""

from tkai.v8.hyper_planning.fabric import HyperPlanningFabric

DASHBOARD_SECTIONS = (
    "Planning Overview",
    "Objectives",
    "Constraints",
    "Scenarios",
    "Simulations",
    "Resources",
    "Schedules",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperPlanningFabric) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, "read_only": True, **fabric.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
