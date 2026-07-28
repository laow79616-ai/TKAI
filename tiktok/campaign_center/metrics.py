"""Prometheus-compatible Campaign Center metrics."""

from __future__ import annotations

METRIC_NAMES = (
    "tiktok_campaigns_total",
    "tiktok_campaign_active_total",
    "tiktok_campaign_completed_total",
    "tiktok_campaign_approvals_total",
    "tiktok_campaign_success_rate",
    "tiktok_campaign_latency_seconds",
)


class CampaignMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str, amount: float = 1.0) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "\n".join(f"{key} {value}" for key, value in self.values.items()) + "\n"
