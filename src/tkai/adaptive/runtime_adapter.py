"""Explicit runtime-facing adapter; it does not change the Runtime API."""

from __future__ import annotations

from collections.abc import Sequence

from .manager import AdaptiveRoutingManager
from .models import ProviderSignal, RoutingDecision


class AdaptiveRoutingRuntimeAdapter:
    """Record real attempts and select only when an application opts in."""

    def __init__(self, manager: AdaptiveRoutingManager) -> None:
        self.manager = manager
        self._attempts: set[str] = set()

    def select(self, candidates: Sequence[str]) -> RoutingDecision:
        """Explicitly ask the adaptive manager to rank the supplied candidates."""
        return self.manager.select_provider(candidates)

    def record_attempt(
        self,
        attempt_id: str,
        signal: ProviderSignal,
        *,
        cache_hit: bool = False,
    ) -> None:
        """Record at most one actual provider call; cache hits have no latency."""
        if cache_hit or attempt_id in self._attempts:
            return
        self._attempts.add(attempt_id)
        self.manager.record_signal(signal)

    def shutdown(self) -> None:
        """Release local duplicate-attempt state without touching the manager."""
        self._attempts.clear()
