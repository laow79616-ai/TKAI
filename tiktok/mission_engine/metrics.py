"""Prometheus-compatible mission metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_missions_total",
    "tiktok_missions_running",
    "tiktok_missions_completed",
    "tiktok_missions_failed",
    "tiktok_missions_recovered",
    "tiktok_mission_latency_seconds",
)


class MissionMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown mission metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown mission metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
