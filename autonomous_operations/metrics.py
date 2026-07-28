"""Prometheus-compatible autonomous operations metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "autonomous_operations_total",
    "autonomous_executions_total",
    "autonomous_success_total",
    "autonomous_failures_total",
    "autonomous_rollbacks_total",
    "autonomous_learning_cycles_total",
    "autonomous_latency_seconds",
)


class AutonomousOperationsMetrics:
    """Thread-safe metric accumulator."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown autonomous operations metric: {name}")
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


__all__ = ("METRICS", "AutonomousOperationsMetrics")
