"""Prometheus-compatible Intelligent Decision Center metrics."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_decisions_total",
    "tiktok_decision_recommendations_total",
    "tiktok_decision_approvals_total",
    "tiktok_decision_confidence",
    "tiktok_decision_latency_seconds",
)


class DecisionMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        self.set(name, self.values[name] + amount)

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown decision metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
