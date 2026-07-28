"""Prometheus-compatible metrics for the TikTok Runtime Manager."""

from __future__ import annotations

METRIC_NAMES = (
    "tiktok_runtime_services_total",
    "tiktok_runtime_running_total",
    "tiktok_runtime_restart_total",
    "tiktok_runtime_recovery_total",
    "tiktok_runtime_health_score",
    "tiktok_runtime_startup_seconds",
    "tiktok_runtime_shutdown_seconds",
    "tiktok_runtime_heartbeat_latency_seconds",
)


class RuntimeMetrics:
    def __init__(self) -> None:
        self.values = dict.fromkeys(METRIC_NAMES, 0.0)

    def set(self, name: str, value: int | float) -> None:
        if name not in self.values:
            raise KeyError(f"Unknown runtime metric: {name}")
        self.values[name] = float(value)

    def increment(self, name: str, amount: int | float = 1) -> None:
        self.set(name, self.values[name] + amount)

    def render_prometheus(self) -> str:
        return (
            "\n".join(f"{name} {value}" for name, value in self.values.items()) + "\n"
        )
