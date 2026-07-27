"""Prometheus-compatible metrics for the Enterprise AI Knowledge Graph."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "knowledge_graphs_total",
    "knowledge_entities_total",
    "knowledge_relationships_total",
    "knowledge_queries_total",
    "knowledge_query_latency_seconds",
    "knowledge_reasoning_total",
    "knowledge_lineage_total",
    "knowledge_analytics_total",
)


class KnowledgeGraphMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown knowledge-graph metric: {name}")
        with self._lock:
            self._values[name] += amount

    def observe(self, name: str, value: float) -> None:
        self.increment(name, value)

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} counter\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )
