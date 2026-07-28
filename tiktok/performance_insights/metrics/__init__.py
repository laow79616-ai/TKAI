"""Prometheus-compatible performance insight metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_performance_profiles_total",
    "tiktok_performance_datasets_total",
    "tiktok_performance_metrics_total",
    "tiktok_performance_comparisons_total",
    "tiktok_performance_trends_total",
    "tiktok_performance_anomalies_total",
    "tiktok_performance_forecasts_total",
    "tiktok_performance_insights_total",
    "tiktok_performance_recommendations_total",
    "tiktok_performance_reports_total",
    "tiktok_performance_analysis_seconds",
    "tiktok_performance_data_freshness_seconds",
    "tiktok_performance_confidence",
)


class PerformanceMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str) -> None:
        self._check(name)
        self.values[name] += 1

    def set(self, name: str, value: float) -> None:
        self._check(name)
        self.values[name] = value

    @staticmethod
    def _check(name: str) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown performance metric: {name}")

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} gauge\n{name} {self.values[name]:g}\n"
            for name in METRIC_NAMES
        )
