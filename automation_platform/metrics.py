"""Prometheus-compatible automation metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "automation_total",
    "automation_runs_total",
    "automation_failures_total",
    "automation_retries_total",
    "automation_duration_seconds",
)


class AutomationMetrics:
    """Thread-safe counters and duration accumulator."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown automation metric: {name}")
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


__all__ = ("METRICS", "AutomationMetrics")
