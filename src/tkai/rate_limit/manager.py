"""Facade joining local quotas, strategy mechanics, and shared EventBus events."""

from __future__ import annotations

from threading import RLock

from tkai.observability import EventBus

from .events import QuotaConsumed, QuotaReset, RateLimitEvent, RateLimitExceeded
from .limiter import RateLimiter
from .models import RateLimitSnapshot
from .registry import QuotaRegistry
from .strategy import RateLimitStrategy, SlidingWindowStrategy


class RateLimitManager:
    """Manage local quota state without ProviderManager or network ownership."""

    def __init__(
        self,
        registry: QuotaRegistry | None = None,
        strategy: RateLimitStrategy | None = None,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry or QuotaRegistry()
        self.strategy = strategy or SlidingWindowStrategy()
        self.limiter = RateLimiter(self.registry, self.strategy)
        self.event_bus = event_bus
        self.events: list[RateLimitEvent] = []
        self._lock = RLock()

    def register(self, snapshot: RateLimitSnapshot) -> None:
        """Register one immutable provider/scope quota."""
        self.registry.register(snapshot)
        self.registry.update(self.strategy.reset(snapshot))

    def list(self) -> list[RateLimitSnapshot]:
        """Return stable local quota snapshots."""
        return self.registry.list()

    def allow(self, provider: str, *, scope: str = "provider", tokens: int = 0) -> bool:
        """Check a quota without consuming capacity or publishing an event."""
        with self._lock:
            return self.limiter.allow(provider, scope=scope, tokens=tokens)

    def consume(
        self, provider: str, *, scope: str = "provider", tokens: int = 0
    ) -> bool:
        """Consume local capacity and publish a safe quota decision event."""
        with self._lock:
            allowed, snapshot = self.limiter.consume(
                provider, scope=scope, tokens=tokens
            )
            event_type: type[RateLimitEvent] = (
                QuotaConsumed if allowed else RateLimitExceeded
            )
            self._publish(
                event_type(
                    provider=provider,
                    scope=scope,
                    snapshot=snapshot,
                    data={
                        "provider": provider,
                        "scope": scope,
                        "snapshot": snapshot.to_dict(),
                    },
                )
            )
        return allowed

    def reset(self, provider: str, *, scope: str = "provider") -> RateLimitSnapshot:
        """Reset one local quota and publish a safe reset event."""
        with self._lock:
            snapshot = self.limiter.reset(provider, scope=scope)
            self._publish(
                QuotaReset(
                    provider=provider,
                    scope=scope,
                    snapshot=snapshot,
                    data={
                        "provider": provider,
                        "scope": scope,
                        "snapshot": snapshot.to_dict(),
                    },
                )
            )
        return snapshot

    def _publish(self, event: RateLimitEvent) -> None:
        """Retain and optionally publish through the existing shared EventBus."""
        self.events.append(event)
        if self.event_bus is not None:
            self.event_bus.publish(event)
