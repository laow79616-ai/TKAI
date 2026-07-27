"""Prometheus-compatible Enterprise AI Integration Hub metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "integration_hub_connectors_total",
    "integration_hub_instances_total",
    "integration_hub_runs_total",
    "integration_hub_failures_total",
    "integration_hub_retries_total",
    "integration_hub_dead_letter_total",
    "integration_hub_latency_seconds",
    "integration_hub_healthy_connectors",
)


class IntegrationHubMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown integration-hub metric: {name}")
        with self._lock:
            self._values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown integration-hub metric: {name}")
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        gauges = {
            "integration_hub_latency_seconds",
            "integration_hub_healthy_connectors",
        }
        return "".join(
            f"# TYPE {name} {'gauge' if name in gauges else 'counter'}\n"
            f"{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )
