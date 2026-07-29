"""Prometheus-compatible autonomous planning metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_autonomous_planning_profiles_total",
    "tiktok_autonomous_planning_plans_total",
    "tiktok_autonomous_planning_steps_total",
    "tiktok_autonomous_planning_simulations_total",
    "tiktok_autonomous_planning_validation_failures_total",
    "tiktok_autonomous_planning_recommendations_total",
    "tiktok_autonomous_planning_reviews_total",
    "tiktok_autonomous_planning_approvals_total",
    "tiktok_autonomous_planning_plan_quality",
    "tiktok_autonomous_planning_constraint_compliance",
    "tiktok_autonomous_planning_resource_feasibility",
    "tiktok_autonomous_planning_schedule_feasibility",
    "tiktok_autonomous_planning_analysis_seconds",
)


class PlanningMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str) -> None:
        self._check(name)
        self.values[name] += 1

    def observe(self, name: str, value: float) -> None:
        self._check(name)
        self.values[name] = max(0.0, value)

    @staticmethod
    def _check(name: str) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown autonomous planning metric: {name}")

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
