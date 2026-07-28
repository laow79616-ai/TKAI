"""Prometheus-compatible Resource Center telemetry."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_resources_total",
    "tiktok_resource_allocations_total",
    "tiktok_resource_reservations_total",
    "tiktok_resource_leases_total",
    "tiktok_resource_capacity_total",
    "tiktok_resource_utilization_ratio",
    "tiktok_resource_health_score",
    "tiktok_resource_recovery_total",
)


class ResourceMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown Resource Center metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown Resource Center metric: {name}")
        self.values[name] = max(0, value)

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
