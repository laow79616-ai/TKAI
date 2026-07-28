"""Knowledge platform metrics."""

from collections import Counter

METRICS = (
    "knowledge_bases_total",
    "knowledge_documents_total",
    "ingestion_jobs_total",
    "ingestion_failures_total",
    "retrieval_queries_total",
    "retrieval_failures_total",
    "retrieval_duration_seconds",
    "citation_results_total",
)


class KnowledgeMetrics:
    def __init__(self) -> None:
        self.values: Counter[str] = Counter({name: 0 for name in METRICS})

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise ValueError("Unknown knowledge metric.")
        self.values[name] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{key} {value}\n" for key, value in self.snapshot().items())
