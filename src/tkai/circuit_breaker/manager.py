"""Facade coordinating breaker registry, strategy, and passive health events."""

from __future__ import annotations

from tkai.health import HealthEvent, HealthStatus

from .breaker import CircuitBreaker
from .errors import CircuitBreakerNotFoundError
from .models import CircuitBreakerSnapshot
from .registry import CircuitBreakerRegistry
from .strategy import CircuitBreakerStrategy, ThresholdStrategy


class CircuitBreakerManager:
    """Update registered breakers using local outcomes and passive health events."""

    def __init__(
        self,
        registry: CircuitBreakerRegistry | None = None,
        strategy: CircuitBreakerStrategy | None = None,
    ) -> None:
        self.registry = registry or CircuitBreakerRegistry()
        self.strategy = strategy or ThresholdStrategy()

    def register(self, provider: str) -> CircuitBreaker:
        """Register a new provider breaker using this manager's default strategy."""
        return self.registry.register(
            provider, CircuitBreaker(provider, strategy=self.strategy)
        )

    def get(self, provider: str) -> CircuitBreaker:
        """Return one provider breaker."""
        return self.registry.get(provider)

    def list(self) -> list[CircuitBreakerSnapshot]:
        """Return stable immutable snapshots for all registered providers."""
        return [breaker.snapshot for breaker in self.registry.list()]

    def reset(self, provider: str) -> None:
        """Reset one provider breaker."""
        self.registry.reset(provider)

    def clear(self) -> None:
        """Clear all provider breakers."""
        self.registry.clear()

    def record_success(self, provider: str) -> CircuitBreakerSnapshot:
        """Record a passive successful provider outcome."""
        return self._ensure(provider).record_success()

    def record_failure(
        self, provider: str, *, reason: str | None = None
    ) -> CircuitBreakerSnapshot:
        """Record a passive failed provider outcome."""
        return self._ensure(provider).record_failure(reason=reason)

    def allow_request(self, provider: str) -> bool:
        """Return whether the provider's breaker currently admits a request."""
        return self._ensure(provider).allow_request()

    def handle_health_event(self, event: HealthEvent) -> CircuitBreakerSnapshot:
        """Consume a passive HealthEvent without inspecting or probing a provider."""
        breaker = self._ensure(event.provider)
        if event.event == "ProviderReset":
            breaker.reset()
        elif (
            event.event == "ProviderUnhealthy"
            or event.new_status is HealthStatus.UNHEALTHY
        ):
            breaker.force_open(reason=event.event)
        elif (
            event.event == "ProviderDegraded"
            or event.new_status is HealthStatus.DEGRADED
        ):
            breaker.record_failure(reason=event.event)
        elif (
            event.event == "ProviderRecovered"
            or event.new_status is HealthStatus.HEALTHY
        ):
            breaker.record_success()
        return breaker.snapshot

    def _ensure(self, provider: str) -> CircuitBreaker:
        """Find or locally register a breaker for an incoming passive event."""
        try:
            return self.registry.get(provider)
        except CircuitBreakerNotFoundError:
            return self.register(provider)
