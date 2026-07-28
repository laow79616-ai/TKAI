"""Prometheus-compatible Automation Engine metrics."""

from __future__ import annotations

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_automation_total",
    "tiktok_automation_running",
    "tiktok_automation_success",
    "tiktok_automation_failures",
    "tiktok_automation_retries",
    "tiktok_automation_recoveries",
    "tiktok_automation_execution_seconds",
)


class AutomationMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown automation metric: {name}")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in METRIC_NAMES:
            raise ValueError(f"Unknown automation metric: {name}")
        self.values[name] = value

    def render_prometheus(self) -> str:
        return (
            "\n".join(
                f"# TYPE {name} gauge\n{name} {self.values[name]:g}"
                for name in METRIC_NAMES
            )
            + "\n"
        )
