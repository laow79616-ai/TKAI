"""Prometheus-compatible super intelligence metrics."""

from collections import defaultdict

METRICS = (
    "super_intelligence_profiles_total",
    "super_reasoning_total",
    "super_predictions_total",
    "super_optimizations_total",
    "super_self_improvements_total",
    "super_evaluations_total",
    "super_latency_seconds",
)


class SuperIntelligenceMetrics:
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
