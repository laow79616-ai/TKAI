"""Prometheus-compatible scheduler telemetry."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_scheduler_tasks_total",
    "tiktok_scheduler_queued_total",
    "tiktok_scheduler_running_total",
    "tiktok_scheduler_completed_total",
    "tiktok_scheduler_failed_total",
    "tiktok_scheduler_retry_total",
    "tiktok_scheduler_recovery_total",
    "tiktok_scheduler_dead_letter_total",
    "tiktok_scheduler_queue_depth",
    "tiktok_scheduler_worker_utilization",
    "tiktok_scheduler_queue_wait_seconds",
    "tiktok_scheduler_execution_seconds",
    "tiktok_scheduler_latency_seconds",
)


class SchedulerMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown scheduler metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown scheduler metric: {name}")
        self.values[name] = max(0, value)

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
