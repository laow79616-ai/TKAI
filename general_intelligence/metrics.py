"""Prometheus-compatible general intelligence metrics."""

from __future__ import annotations

from collections import defaultdict

METRICS = (
    "general_intelligence_profiles_total",
    "general_reasoning_total",
    "general_predictions_total",
    "general_learning_cycles_total",
    "general_evaluations_total",
    "general_adaptations_total",
    "general_execution_total",
    "general_failures_total",
    "general_latency_seconds",
)


class GeneralIntelligenceMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)

    def increment(self, name: str, value: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(name)
        self._values[name] += value

    def snapshot(self) -> dict[str, float]:
        return {name: self._values[name] for name in METRICS}

    def render_prometheus(self) -> str:
        return "\n".join(f"{name} {value}" for name, value in self.snapshot().items())
