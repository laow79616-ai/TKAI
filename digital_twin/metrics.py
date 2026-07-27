"""Prometheus-compatible metrics for the Enterprise AI Digital Twin Platform."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "digital_twins_total",
    "twin_sync_total",
    "twin_sync_failures_total",
    "simulation_runs_total",
    "prediction_total",
    "optimization_total",
)


class DigitalTwinMetrics:
    """Thread-safe metric registry."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown digital-twin metric: {name}")
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
