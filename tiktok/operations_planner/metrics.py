"""Prometheus-compatible operations planner metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_operations_plans_total",
    "tiktok_operations_plans_proposed_total",
    "tiktok_operations_plans_approved_total",
    "tiktok_operations_plans_rejected_total",
    "tiktok_operations_plans_executed_total",
    "tiktok_operations_plan_failures_total",
    "tiktok_operations_plan_simulations_total",
    "tiktok_operations_plan_recommendations_total",
    "tiktok_operations_plan_latency_seconds",
    "tiktok_operations_plan_confidence",
)


class PlannerMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown planner metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown planner metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
