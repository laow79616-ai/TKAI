"""Prometheus-compatible Knowledge Evolution Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_knowledge_profiles_total",
    "tiktok_knowledge_versions_total",
    "tiktok_knowledge_recommendations_total",
    "tiktok_knowledge_confidence",
    "tiktok_knowledge_latency_seconds",
)


class KnowledgeMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown knowledge metric: {name}")
        self.values[name] += 1

    def observe(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown knowledge metric: {name}")
        self.values[name] = max(0.0, value)

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
