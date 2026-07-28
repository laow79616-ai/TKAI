"""Prometheus-compatible autonomous intelligence metrics."""

from __future__ import annotations

from collections import defaultdict

METRICS = (
    "autonomous_intelligence_profiles_total",
    "autonomous_reasoning_total",
    "autonomous_predictions_total",
    "autonomous_learning_cycles_total",
    "autonomous_adaptations_total",
    "autonomous_execution_total",
    "autonomous_latency_seconds",
)


class AutonomousIntelligenceMetrics:
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
