"""Prometheus-compatible metrics for predictive analytics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_predictive_profiles_total",
    "tiktok_predictive_forecasts_total",
    "tiktok_predictive_trends_total",
    "tiktok_predictive_recommendations_total",
    "tiktok_predictive_latency_seconds",
    "tiktok_predictive_confidence",
)


class PredictiveMetrics:
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
            raise ValueError(f"Unknown predictive metric: {name}")

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
