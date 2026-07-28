"""Prometheus-compatible metrics for enterprise AI operations."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "operations_jobs_total",
    "backup_total",
    "restore_total",
    "health_checks_total",
    "diagnostic_runs_total",
    "capacity_alerts_total",
    "notifications_total",
)


class OperationsMetrics:
    """Thread-safe counters used by the operations platform."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown operations metric: {name}")
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


__all__ = ("METRICS", "OperationsMetrics")
