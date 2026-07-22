"""Facade for passive collection, local load evaluation, and EventBus subscription."""

from __future__ import annotations

from tkai.observability import EventBus

from .collector import PassiveLoadCollector
from .evaluator import LoadEvaluator
from .models import ProviderLoadSnapshot
from .registry import LoadRegistry


class LoadManager:
    """Own local load registry and collector without accessing provider networks."""

    def __init__(
        self,
        registry: LoadRegistry | None = None,
        evaluator: LoadEvaluator | None = None,
        *,
        capacity: int = 10,
        max_latency_samples: int = 256,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry or LoadRegistry()
        self.evaluator = evaluator or LoadEvaluator()
        self.collector = PassiveLoadCollector(
            self.registry,
            self.evaluator,
            capacity=capacity,
            max_latency_samples=max_latency_samples,
            event_bus=event_bus,
        )

    def subscribe(self, event_bus: EventBus) -> None:
        """Attach collection to the existing shared EventBus."""
        self.collector.subscribe(event_bus)

    def list(self) -> list[ProviderLoadSnapshot]:
        """Return stable immutable snapshots."""
        return self.registry.list()

    def get(self, provider: str) -> ProviderLoadSnapshot:
        """Return one immutable provider snapshot."""
        return self.registry.get(provider)

    def reset(self, provider: str) -> ProviderLoadSnapshot:
        """Reset one local provider snapshot."""
        return self.collector.reset(provider)

    def clear(self) -> None:
        """Clear all local load snapshots and bounded latency samples."""
        self.collector.clear()
