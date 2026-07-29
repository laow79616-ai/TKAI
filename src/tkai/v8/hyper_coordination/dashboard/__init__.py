"""Read-only dashboard model for Hyper Coordination."""

from __future__ import annotations

from tkai.v8.hyper_coordination.coordination import HyperCoordinationFramework

DASHBOARD_SECTIONS = (
    "Coordination Overview",
    "Framework Registry",
    "Dependencies",
    "Relationships",
    "Synchronization",
    "Compatibility",
    "Governance",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(
    framework: HyperCoordinationFramework,
) -> dict[str, object]:
    """Build the complete dashboard projection without mutating state."""

    return {"sections": DASHBOARD_SECTIONS, **framework.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
