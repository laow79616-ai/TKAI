"""Prometheus-compatible Autonomous Operation Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_autonomous_missions_total",
    "tiktok_autonomous_running",
    "tiktok_autonomous_success",
    "tiktok_autonomous_failures",
    "tiktok_autonomous_recoveries",
    "tiktok_autonomous_latency_seconds",
)


class AutonomousMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown autonomous-operation metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown autonomous-operation metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
