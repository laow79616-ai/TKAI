"""Read-only adaptive-routing diagnostic helpers independent of the AI Doctor."""

from __future__ import annotations

from dataclasses import dataclass

from .manager import AdaptiveRoutingManager


@dataclass(frozen=True, slots=True)
class AdaptiveDiagnostic:
    """One stable, safe adaptive-routing diagnostic summary."""

    status: str
    message: str
    detail: dict[str, object]


def diagnose(manager: AdaptiveRoutingManager | None) -> AdaptiveDiagnostic:
    """Inspect local adaptive state only; no provider invocation is performed."""
    if manager is None:
        return AdaptiveDiagnostic(
            "WARNING",
            "No AdaptiveRoutingManager was supplied",
            {"enabled_routers": 0, "signal_count": 0},
        )
    snapshot = manager.snapshot()
    statistics = snapshot["statistics"]
    values = statistics if isinstance(statistics, list) else []
    routers = snapshot["routers"]
    router_values = routers if isinstance(routers, list) else []
    signal_count = sum(
        item["sample_count"]
        for item in values
        if isinstance(item, dict) and isinstance(item.get("sample_count"), int)
    )
    return AdaptiveDiagnostic(
        "PASS",
        "Adaptive routing history and scoring are available",
        {
            "enabled_routers": sum(
                item["enabled"]
                for item in router_values
                if isinstance(item, dict) and isinstance(item.get("enabled"), bool)
            ),
            "signal_count": signal_count,
            "weights": snapshot["weights"],
        },
    )
