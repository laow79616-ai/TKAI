"""Prometheus-compatible self-optimization platform metrics."""

from __future__ import annotations

from collections import defaultdict

METRICS = (
    "self_optimization_profiles_total",
    "self_optimization_cycles_total",
    "self_performance_improvements_total",
    "self_cost_reduction_total",
    "self_latency_improvements_total",
    "self_capacity_adjustments_total",
    "self_optimization_latency_seconds",
)


class SelfOptimizationMetrics:
    """Dependency-free metric registry for the optimization control plane."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)

    def increment(self, name: str, value: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(name)
        if value < 0:
            raise ValueError("Metric increments cannot be negative.")
        self._values[name] += value

    def snapshot(self) -> dict[str, float]:
        return {name: self._values[name] for name in METRICS}

    def render_prometheus(self) -> str:
        return "\n".join(f"{name} {value}" for name, value in self.snapshot().items())
