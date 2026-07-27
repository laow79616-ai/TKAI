"""Prometheus-compatible Enterprise AI Integration Platform metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "integrations_total",
    "integration_requests_total",
    "integration_failures_total",
    "integration_retries_total",
    "integration_latency_seconds",
    "webhook_deliveries_total",
    "webhook_failures_total",
    "dead_letter_total",
)


class IntegrationMetrics:
    """Thread-safe counters and latency accumulator."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown integration metric: {name}")
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


__all__ = ("METRICS", "IntegrationMetrics")
