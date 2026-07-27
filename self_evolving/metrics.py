"""Prometheus-compatible self-evolving platform metrics."""

from __future__ import annotations

from collections import defaultdict

METRICS = (
    "self_evolving_profiles_total",
    "self_evolution_cycles_total",
    "self_learning_cycles_total",
    "self_experiments_total",
    "self_optimizations_total",
    "self_rollbacks_total",
    "self_latency_seconds",
)


class SelfEvolvingMetrics:
    """Small dependency-free metric registry used by the control plane."""

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
