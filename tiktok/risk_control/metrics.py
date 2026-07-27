"""Small Prometheus-compatible metric registry."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_risk_profiles_total",
    "tiktok_risk_events_total",
    "tiktok_risk_alerts_total",
    "tiktok_risk_accounts_paused_total",
    "tiktok_risk_workspaces_paused_total",
    "tiktok_risk_restrictions_total",
    "tiktok_risk_recovery_total",
    "tiktok_risk_recovery_success_total",
    "tiktok_risk_score",
    "tiktok_risk_evaluation_latency_seconds",
)


class RiskMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown risk metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown risk metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
