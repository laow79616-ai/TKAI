"""Deterministic, explainable adaptive provider scoring."""

from __future__ import annotations

from .history import ProviderHistory
from .models import ProviderScore, ProviderSignal, ProviderStatistics
from .weights import AdaptiveWeights


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


class AdaptiveScoringEngine:
    """Score bounded historical signals without random or machine-learning logic."""

    def __init__(
        self,
        history: ProviderHistory,
        weights: AdaptiveWeights | None = None,
        *,
        minimum_samples: int = 3,
    ) -> None:
        if minimum_samples < 1:
            raise ValueError("minimum_samples must be positive")
        self.history = history
        self.weights = (weights or AdaptiveWeights()).normalized()
        self.minimum_samples = minimum_samples

    def score(self, provider: str) -> ProviderScore:
        """Return a normalized, explainable score for one named provider."""
        stats = self.history.statistics(provider)
        latest = self.history.snapshot(provider)
        signal = latest[-1] if latest else None
        eligible, reasons = self._eligibility(signal)
        component_scores = self._components(stats, signal)
        total = sum(
            getattr(self.weights, name) * component_scores[name]
            for name in ("reliability", "latency", "cost", "load", "health")
        )
        confidence = _clamp(stats.sample_count / self.minimum_samples)
        if stats.sample_count < self.minimum_samples:
            reasons.append("limited history")
        if not eligible:
            total = 0.0
        return ProviderScore(
            provider=provider,
            total_score=_clamp(total),
            latency_score=component_scores["latency"],
            reliability_score=component_scores["reliability"],
            cost_score=component_scores["cost"],
            load_score=component_scores["load"],
            health_score=component_scores["health"],
            confidence=confidence,
            eligible=eligible,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _eligibility(signal: ProviderSignal | None) -> tuple[bool, list[str]]:
        if signal is None:
            return True, ["cold start"]
        if signal.breaker_open:
            return False, ["circuit breaker open"]
        if not signal.available:
            return False, ["provider unavailable"]
        return True, []

    @staticmethod
    def _components(
        stats: ProviderStatistics, signal: ProviderSignal | None
    ) -> dict[str, float]:
        if stats.sample_count == 0:
            return {
                "reliability": 0.5,
                "latency": 0.5,
                "cost": 0.5,
                "load": 0.5,
                "health": 0.5,
            }
        health = 1.0
        if signal is not None and signal.rate_limited:
            health = 0.25
        return {
            "reliability": _clamp(stats.success_rate),
            "latency": _clamp(1.0 / (1.0 + stats.average_latency_ms / 1000.0)),
            "cost": _clamp(1.0 / (1.0 + stats.average_cost)),
            "load": _clamp(1.0 - stats.current_load),
            "health": health,
        }
