"""Prometheus-compatible metrics for continuous optimization."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_optimization_profiles_total",
    "tiktok_optimization_candidates_total",
    "tiktok_optimization_experiments_total",
    "tiktok_optimization_recommendations_total",
    "tiktok_optimization_approvals_total",
    "tiktok_optimization_changes_total",
    "tiktok_optimization_success_total",
    "tiktok_optimization_failures_total",
    "tiktok_optimization_rollbacks_total",
    "tiktok_optimization_regressions_total",
    "tiktok_optimization_improvement_ratio",
    "tiktok_optimization_confidence",
    "tiktok_optimization_analysis_seconds",
    "tiktok_optimization_validation_seconds",
)


class OptimizationMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown optimization metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown optimization metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
