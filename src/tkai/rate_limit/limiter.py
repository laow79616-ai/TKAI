"""Local quota consumption facade that delegates mechanics to a strategy."""

from __future__ import annotations

from .models import RateLimitSnapshot
from .registry import QuotaRegistry
from .strategy import RateLimitStrategy


class RateLimiter:
    """Read and update registered local quotas without accessing providers."""

    def __init__(self, registry: QuotaRegistry, strategy: RateLimitStrategy) -> None:
        self.registry = registry
        self.strategy = strategy

    def allow(self, provider: str, *, scope: str = "provider", tokens: int = 0) -> bool:
        """Return whether a registered quota permits another local request."""
        return self.strategy.allow(self.registry.get(provider, scope), tokens=tokens)

    def consume(
        self, provider: str, *, scope: str = "provider", tokens: int = 0
    ) -> tuple[bool, RateLimitSnapshot]:
        """Consume local capacity if permitted and persist the new snapshot."""
        snapshot = self.registry.get(provider, scope)
        allowed = self.strategy.allow(snapshot, tokens=tokens)
        updated = self.strategy.consume(snapshot, tokens=tokens)
        self.registry.update(updated)
        return allowed, updated

    def reset(self, provider: str, *, scope: str = "provider") -> RateLimitSnapshot:
        """Reset strategy-local usage while preserving registered quota limits."""
        snapshot = self.registry.get(provider, scope)
        updated = self.strategy.reset(snapshot)
        self.registry.update(updated)
        return updated
