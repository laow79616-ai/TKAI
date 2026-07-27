"""Prometheus-compatible Content Center metrics."""

from __future__ import annotations

METRICS = (
    "tiktok_content_projects_total",
    "tiktok_media_assets_total",
    "tiktok_drafts_total",
    "tiktok_publish_queue_total",
    "tiktok_publish_success_total",
    "tiktok_publish_failures_total",
    "tiktok_publish_latency_seconds",
)


class ContentMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return (
            "\n".join(f"{name} {value}" for name, value in self.values.items()) + "\n"
        )
