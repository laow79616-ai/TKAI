"""Facade for routing metadata registration and read-only provider selection."""

from __future__ import annotations

from tkai.circuit_breaker import CircuitBreakerRegistry
from tkai.health import HealthRegistry

from .models import ProviderMetadata, RoutingDecision
from .registry import RoutingRegistry
from .router import ProviderRouter
from .strategy import CostAwareStrategy, RoutingStrategy


class RoutingManager:
    """Own routing registry and router without changing ProviderManager behavior."""

    def __init__(
        self,
        registry: RoutingRegistry | None = None,
        strategy: RoutingStrategy | None = None,
        *,
        health_registry: HealthRegistry | None = None,
        breaker_registry: CircuitBreakerRegistry | None = None,
    ) -> None:
        self.registry = registry or RoutingRegistry()
        self.strategy = strategy or CostAwareStrategy()
        self.router = ProviderRouter(
            self.registry,
            self.strategy,
            health_registry=health_registry,
            breaker_registry=breaker_registry,
        )

    def register(self, metadata: ProviderMetadata) -> None:
        """Register immutable provider routing metadata."""
        self.registry.register(metadata)

    def get(self, provider: str) -> ProviderMetadata:
        """Return one provider's routing metadata."""
        return self.registry.get(provider)

    def list(self) -> list[ProviderMetadata]:
        """Return routing metadata in stable provider-name order."""
        return self.registry.list()

    def remove(self, provider: str) -> ProviderMetadata:
        """Remove and return one provider's routing metadata."""
        return self.registry.remove(provider)

    def clear(self) -> None:
        """Clear all routing metadata."""
        self.registry.clear()

    def route(
        self, *, required_capabilities: frozenset[str] = frozenset()
    ) -> RoutingDecision:
        """Select a passive provider candidate through the configured strategy."""
        return self.router.route(required_capabilities=required_capabilities)
