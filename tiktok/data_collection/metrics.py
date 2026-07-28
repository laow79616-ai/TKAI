"""Prometheus-compatible TikTok collection metrics."""

from __future__ import annotations

METRICS = (
    "tiktok_collection_projects_total",
    "tiktok_collection_jobs_total",
    "tiktok_collection_success_total",
    "tiktok_collection_failure_total",
    "tiktok_dataset_total",
    "tiktok_collection_latency_seconds",
)


class CollectionMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        lines = [
            "# HELP tiktok_collection_latency_seconds Last collection latency.",
            "# TYPE tiktok_collection_latency_seconds gauge",
        ]
        lines.extend(f"{name} {value}" for name, value in self.values.items())
        return "\n".join(lines) + "\n"
