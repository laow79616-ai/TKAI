"""Prometheus-compatible Decision Evolution Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_decision_evolution_profiles_total",
    "tiktok_decision_evolution_decisions_total",
    "tiktok_decision_evolution_outcomes_total",
    "tiktok_decision_evolution_patterns_total",
    "tiktok_decision_evolution_recommendations_total",
    "tiktok_decision_evolution_reviews_total",
    "tiktok_decision_evolution_quality_score",
    "tiktok_decision_evolution_confidence_calibration",
    "tiktok_decision_evolution_evidence_completeness",
    "tiktok_decision_evolution_analysis_seconds",
)


class DecisionEvolutionMetrics:
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
            raise ValueError(f"Unknown decision-evolution metric: {name}")

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
