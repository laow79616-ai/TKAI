"""Explicit local routing foundation example without ProviderManager takeover."""

from __future__ import annotations

from tkai.health import HealthRegistry, HealthSnapshot, HealthStatus
from tkai.routing import ProviderMetadata, RoutingManager


def run() -> str | None:
    """Choose the lower-cost healthy provider through an explicit router instance."""
    health = HealthRegistry()
    health.update(HealthSnapshot("primary", status=HealthStatus.HEALTHY))
    health.update(HealthSnapshot("backup", status=HealthStatus.HEALTHY))
    manager = RoutingManager(health_registry=health)
    manager.register(
        ProviderMetadata(
            "primary", prompt_cost_per_1k=0.5, capabilities=frozenset({"chat"})
        )
    )
    manager.register(
        ProviderMetadata(
            "backup", prompt_cost_per_1k=0.1, capabilities=frozenset({"chat"})
        )
    )
    return manager.route(required_capabilities=frozenset({"chat"})).selected_provider


if __name__ == "__main__":
    print(run())
