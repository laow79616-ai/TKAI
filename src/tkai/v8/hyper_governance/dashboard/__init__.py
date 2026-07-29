"""Read-only dashboard projection for Hyper Governance."""

from __future__ import annotations

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric

DASHBOARD_SECTIONS = (
    "Governance Overview",
    "Policies",
    "Constraints",
    "Compliance",
    "Reviews",
    "Approvals",
    "Compatibility",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperGovernanceFabric) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "read_only": True,
        **fabric.snapshot(),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
