"""Thread-safe metrics for the Enterprise AI Command Center."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "command_center_instances_total",
    "active_operations_total",
    "active_alerts_total",
    "active_incidents_total",
    "automation_tasks_total",
    "command_center_latency_seconds",
    "topology_nodes_total",
    "health_checks_total",
)


class CommandCenterMetrics:
    """Small Prometheus-compatible metrics registry."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def set(self, name: str, value: float) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown Command Center metric: {name}")
        with self._lock:
            self._values[name] = value

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown Command Center metric: {name}")
        with self._lock:
            self._values[name] += amount

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} gauge\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )
