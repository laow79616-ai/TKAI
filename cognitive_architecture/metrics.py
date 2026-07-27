"""Prometheus-compatible cognitive architecture metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "cognitive_models_total",
    "cognitive_reasoning_total",
    "cognitive_learning_cycles_total",
    "cognitive_reflections_total",
    "cognitive_decisions_total",
    "cognitive_latency_seconds",
    "cognitive_failures_total",
)


class CognitiveMetrics:
    """Thread-safe metric registry with a stable public contract."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown cognitive metric: {name}")
        with self._lock:
            self._values[name] += amount

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} counter\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )


__all__ = ("CognitiveMetrics", "METRICS")
