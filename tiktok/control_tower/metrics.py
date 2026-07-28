"""Prometheus-compatible Control Tower metrics."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_control_tower_health",
    "tiktok_control_tower_runtime",
    "tiktok_control_tower_resources",
    "tiktok_control_tower_alerts",
    "tiktok_control_tower_latency_seconds",
)


class ControlTowerMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown Control Tower metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
