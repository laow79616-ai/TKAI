"""Metrics for TikTok account farming."""

from __future__ import annotations

METRICS = (
    "tiktok_farming_plans_total",
    "tiktok_farming_active_total",
    "tiktok_farming_executions_total",
    "tiktok_farming_success_total",
    "tiktok_farming_failures_total",
    "tiktok_farming_pauses_total",
    "tiktok_farming_approvals_total",
    "tiktok_farming_risk_events_total",
    "tiktok_farming_latency_seconds",
)


class FarmingMetrics:
    def __init__(self) -> None:
        self.values = {name: 0.0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "\n".join(f"{key} {value}" for key, value in self.values.items()) + "\n"
