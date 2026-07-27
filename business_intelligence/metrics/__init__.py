"""Business metric definitions and Prometheus-compatible telemetry."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "bi_workspaces_total",
    "bi_data_sources_total",
    "bi_datasets_total",
    "bi_queries_total",
    "bi_query_failures_total",
    "bi_query_latency_seconds",
    "bi_reports_total",
    "bi_dashboards_total",
    "bi_insights_total",
    "bi_alerts_total",
    "bi_exports_total",
)


class BusinessIntelligenceMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown BI metric: {name}")
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
