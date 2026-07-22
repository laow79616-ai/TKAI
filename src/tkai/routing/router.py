"""Read-only router joining metadata with Health and Circuit Breaker state."""

from __future__ import annotations

from tkai.circuit_breaker import (
    CircuitBreakerNotFoundError,
    CircuitBreakerRegistry,
    CircuitState,
)
from tkai.health import HealthRegistry, HealthStatus

from .models import RoutingCandidate, RoutingDecision
from .registry import RoutingRegistry
from .strategy import RoutingStrategy


class ProviderRouter:
    """Build passive candidates then delegate deterministic selection to a strategy."""

    def __init__(
        self,
        registry: RoutingRegistry,
        strategy: RoutingStrategy,
        *,
        health_registry: HealthRegistry | None = None,
        breaker_registry: CircuitBreakerRegistry | None = None,
    ) -> None:
        self.registry = registry
        self.strategy = strategy
        self.health_registry = health_registry
        self.breaker_registry = breaker_registry

    def route(
        self, *, required_capabilities: frozenset[str] = frozenset()
    ) -> RoutingDecision:
        """Return a selection from passive registry snapshots without probing APIs."""
        candidates = tuple(
            self._candidate(metadata.provider) for metadata in self.registry.list()
        )
        return self.strategy.select_provider(
            candidates, required_capabilities=required_capabilities
        )

    def _candidate(self, provider: str) -> RoutingCandidate:
        """Read provider metadata and passive dependent subsystem snapshots."""
        metadata = self.registry.get(provider)
        health = self.health_registry.get(provider) if self.health_registry else None
        breaker_state = CircuitState.CLOSED
        if self.breaker_registry is not None:
            try:
                breaker_state = self.breaker_registry.get(provider).snapshot.state
            except CircuitBreakerNotFoundError:
                pass
        return RoutingCandidate(
            metadata,
            health.status if health is not None else HealthStatus.UNKNOWN,
            breaker_state,
        )
