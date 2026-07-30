"""Read-only dashboard projection for Hyper Operations."""

from tkai.v8.hyper_operations.fabric import HyperOperationsFabric

DASHBOARD_SECTIONS = (
    "Operations Overview",
    "Readiness",
    "Runtime",
    "Resources",
    "Dependencies",
    "Recovery",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperOperationsFabric) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, "read_only": True, **fabric.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
