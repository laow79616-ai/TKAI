"""Read-only dashboard projection for Hyper Governance."""

from __future__ import annotations

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh

DASHBOARD_SECTIONS = (
    "Governance Overview",
    "Federation",
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


def dashboard_snapshot(fabric: AdaptiveGovernanceMesh) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "read_only": True,
        **fabric.snapshot(),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
