"""Prometheus-compatible Strategy Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_strategies_total",
    "tiktok_strategies_proposed_total",
    "tiktok_strategies_approved_total",
    "tiktok_strategies_rejected_total",
    "tiktok_strategy_scenarios_total",
    "tiktok_strategy_recommendations_total",
    "tiktok_strategy_handoffs_total",
    "tiktok_strategy_confidence",
    "tiktok_strategy_analysis_seconds",
    "tiktok_strategy_approval_seconds",
)


class StrategyMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown strategy metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown strategy metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
