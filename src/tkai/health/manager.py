"""Facade for passive health state."""

from __future__ import annotations

from .collector import PassiveHealthCollector
from .registry import HealthRegistry


class HealthManager:
    def __init__(self) -> None:
        self.registry = HealthRegistry()
        self.collector = PassiveHealthCollector(self.registry)

    def reset(self, provider: str) -> None:
        """Reset one passive snapshot and record a framework-neutral event."""
        from datetime import datetime, timezone

        from .events import HealthEvent
        from .models import HealthStatus

        old = self.registry.get(provider)
        self.registry.reset(provider)
        self.collector.events.append(
            HealthEvent(
                provider,
                "ProviderReset",
                old.status,
                HealthStatus.UNKNOWN,
                datetime.now(timezone.utc),
            )
        )
