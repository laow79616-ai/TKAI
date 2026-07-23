"""Read-only diagnostics for explicit multi-region wiring."""

from __future__ import annotations

from dataclasses import dataclass

from .manager import MultiRegionManager


@dataclass(frozen=True, slots=True)
class MultiRegionDiagnostic:
    status: str
    message: str
    detail: dict[str, object]


def diagnose(manager: MultiRegionManager | None) -> MultiRegionDiagnostic:
    """Inspect only process-local configuration and never perform a probe."""
    if manager is None:
        return MultiRegionDiagnostic(
            "WARNING",
            "No MultiRegionManager was supplied",
            {"regions": 0, "event_bus": False},
        )
    snapshot = manager.snapshot()
    regions = snapshot["regions"]
    return MultiRegionDiagnostic(
        "PASS",
        "Multi-region registry, topology, and policy are available",
        {
            "regions": len(regions) if isinstance(regions, list) else 0,
            "topology": snapshot["topology"],
            "event_bus": manager.event_bus is not None,
        },
    )
