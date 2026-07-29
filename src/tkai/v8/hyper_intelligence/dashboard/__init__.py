"""Read-only dashboard projection for Hyper Intelligence."""

from __future__ import annotations

from tkai.v8.hyper_intelligence.fabric import HyperIntelligenceFabric

DASHBOARD_SECTIONS = (
    "Hyper Intelligence Overview",
    "Knowledge",
    "Evidence",
    "Signals",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperIntelligenceFabric) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **fabric.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
