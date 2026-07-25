"""Thread-safe facade for explicit adaptive-routing lifecycle and decisions."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from threading import RLock

from tkai.observability import EventBus

from .events import (
    AdaptiveEvent,
    AdaptiveFallbackUsed,
    AdaptiveHistoryCleared,
    AdaptiveNoProviderAvailable,
    AdaptiveProviderRanked,
    AdaptiveProviderSelected,
    AdaptiveScoreCalculated,
    AdaptiveSignalRecorded,
)
from .history import ProviderHistory
from .models import ProviderSignal, ProviderStatistics, RoutingDecision
from .registry import AdaptiveRouterRegistry
from .router import AdaptiveRouter
from .scoring import AdaptiveScoringEngine
from .weights import AdaptiveWeights


class AdaptiveRoutingManager:
    """Own local history and routers without changing legacy routing defaults."""

    def __init__(
        self,
        history: ProviderHistory | None = None,
        weights: AdaptiveWeights | None = None,
        *,
        event_bus: EventBus | None = None,
        minimum_samples: int = 3,
    ) -> None:
        self.history = history or ProviderHistory()
        self.scoring = AdaptiveScoringEngine(
            self.history,
            weights,
            minimum_samples=minimum_samples,
        )
        self.registry = AdaptiveRouterRegistry()
        self.default_router = AdaptiveRouter(self.scoring)
        self.registry.register("default", self.default_router)
        self.event_bus = event_bus
        self.events: list[AdaptiveEvent] = []
        self._lock = RLock()
        self._shutdown = False

    @property
    def weights(self) -> AdaptiveWeights:
        """Return the normalized immutable weights used by the scoring engine."""
        return self.scoring.weights

    def record_signal(self, signal: ProviderSignal) -> None:
        """Store one actual provider outcome and publish a safe local event."""
        with self._lock:
            if self._shutdown:
                return
            self.history.record(signal)
        self._publish(
            AdaptiveSignalRecorded(
                provider=signal.provider,
                candidate_count=1,
                reason="provider attempt recorded",
            )
        )

    def rank_providers(
        self,
        candidates: Sequence[str],
        *,
        router: str = "default",
        context: Mapping[str, object] | None = None,
    ) -> tuple[object, ...]:
        """Return stable adaptive scores while isolating event subscriber failures."""
        selected = self._router(router)
        scores = selected.rank(candidates, context)
        for score in scores:
            self._publish(
                AdaptiveScoreCalculated(
                    provider=score.provider,
                    score=score.total_score,
                    confidence=score.confidence,
                    candidate_count=len(scores),
                    reason="score calculated",
                )
            )
        self._publish(
            AdaptiveProviderRanked(
                candidate_count=len(scores),
                reason="providers ranked",
            )
        )
        return scores

    def select_provider(
        self,
        candidates: Sequence[str],
        *,
        router: str = "default",
        context: Mapping[str, object] | None = None,
    ) -> RoutingDecision:
        """Select an eligible provider only when this facade is explicitly called."""
        selected = self._router(router)
        try:
            decision = selected.select(candidates, context)
        except Exception:
            self._publish(
                AdaptiveNoProviderAvailable(
                    candidate_count=len(candidates),
                    reason="no eligible provider",
                )
            )
            raise
        for score in decision.scores:
            self._publish(
                AdaptiveScoreCalculated(
                    provider=score.provider,
                    score=score.total_score,
                    confidence=score.confidence,
                    candidate_count=len(decision.scores),
                    reason="score calculated for selection",
                )
            )
        event_type: type[AdaptiveEvent] = (
            AdaptiveFallbackUsed if decision.fallback_used else AdaptiveProviderSelected
        )
        self._publish(
            event_type(
                provider=decision.selected_provider,
                selected_provider=decision.selected_provider,
                candidate_count=len(decision.candidates),
                reason=decision.reason,
            )
        )
        return decision

    def statistics(self, provider: str) -> ProviderStatistics:
        """Return a read-only aggregate for one provider."""
        return self.history.statistics(provider)

    def snapshot(self) -> dict[str, object]:
        """Return stable local diagnostics without invoking providers or networks."""
        providers = sorted({signal.provider for signal in self.history.snapshot()})
        return {
            "enabled": not self._shutdown,
            "routers": [
                {"name": name, "enabled": self.registry.enabled(name)}
                for name, _router in self.registry.list()
            ],
            "weights": self.weights.snapshot(),
            "statistics": [
                self.statistics(provider).to_dict() for provider in providers
            ],
        }

    def shutdown(self) -> None:
        """Disable future recording without mutating legacy provider subsystems."""
        with self._lock:
            self._shutdown = True

    def clear(self) -> None:
        """Clear local history and publish an isolated lifecycle event."""
        self.history.clear()
        self._publish(AdaptiveHistoryCleared(reason="local history cleared"))

    def _router(self, name: str) -> AdaptiveRouter:
        router = self.registry.get(name)
        if not self.registry.enabled(name):
            raise RuntimeError(f"Adaptive router '{name}' is disabled")
        if not isinstance(router, AdaptiveRouter):
            raise RuntimeError(f"Adaptive router '{name}' has an invalid type")
        return router

    def _publish(self, event: AdaptiveEvent) -> None:
        with self._lock:
            self.events.append(event)
        if self.event_bus is not None:
            try:
                self.event_bus.publish(event)
            except Exception:
                return
