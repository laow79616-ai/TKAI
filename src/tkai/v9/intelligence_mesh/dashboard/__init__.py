"""Read-only dashboard projection for Hyper Intelligence."""

from __future__ import annotations

from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh

DASHBOARD_SECTIONS = (
    "Intelligence Mesh Overview",
    "Federation",
    "Knowledge",
    "Evidence",
    "Signals",
    "Recommendations",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: AdaptiveIntelligenceMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **fabric.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
