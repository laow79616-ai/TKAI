"""Dependency-free metrics for customer journeys."""

from dataclasses import dataclass, field

METRIC_NAMES = (
    "tiktok_customer_journeys_total",
    "tiktok_customer_conversions_total",
    "tiktok_customer_dropoff_rate",
    "tiktok_customer_completion_rate",
    "tiktok_customer_stage_latency_seconds",
    "tiktok_customer_journey_latency_seconds",
)


@dataclass(slots=True)
class JourneyMetrics:
    values: dict[str, float] = field(
        default_factory=lambda: {name: 0.0 for name in METRIC_NAMES}
    )

    def increment(self, name: str, amount: float = 1.0) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def render_prometheus(self) -> str:
        lines = (f"{name} {value}" for name, value in self.values.items())
        return "\n".join(lines) + "\n"
