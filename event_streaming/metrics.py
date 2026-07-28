"""Prometheus-compatible event-streaming metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "events_published_total",
    "events_consumed_total",
    "event_failures_total",
    "event_retries_total",
    "dead_letter_total",
    "consumer_lag",
    "stream_latency_seconds",
)


class EventStreamingMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown event-streaming metric: {name}")
        with self._lock:
            self._values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown event-streaming metric: {name}")
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        gauges = {"consumer_lag", "stream_latency_seconds"}
        return "".join(
            f"# TYPE {name} "
            f"{'gauge' if name in gauges else 'counter'}\n"
            f"{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )
