"""Prometheus-compatible TikTok operations metrics."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_operations_centers_total",
    "tiktok_operations_active_tasks_total",
    "tiktok_operations_alerts_total",
    "tiktok_operations_incidents_total",
    "tiktok_operations_recoveries_total",
    "tiktok_operations_recovery_success_total",
    "tiktok_operations_actions_total",
    "tiktok_operations_action_failures_total",
    "tiktok_operations_health_score",
    "tiktok_operations_latency_seconds",
)


class OperationsMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown operations metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown operations metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
