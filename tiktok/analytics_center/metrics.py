"""Prometheus-compatible analytics metrics."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_reports_total",
    "tiktok_kpis_total",
    "tiktok_trends_total",
    "tiktok_forecasts_total",
    "tiktok_insights_total",
    "tiktok_report_latency_seconds",
)


class AnalyticsMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown analytics metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown analytics metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
