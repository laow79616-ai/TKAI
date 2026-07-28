"""Prometheus-compatible Creator Workspace metrics."""

from __future__ import annotations

METRIC_NAMES = (
    "tiktok_creator_projects_total",
    "tiktok_creator_assets_total",
    "tiktok_creator_reviews_total",
    "tiktok_creator_approvals_total",
    "tiktok_creator_publish_plan_total",
    "tiktok_creator_latency_seconds",
)


class CreatorMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        lines = (f"{name} {value}" for name, value in self.values.items())
        return "\n".join(lines) + "\n"
