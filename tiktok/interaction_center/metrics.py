"""Prometheus-compatible Interaction Center metrics."""

from __future__ import annotations


class InteractionMetrics:
    NAMES = (
        "tiktok_interaction_projects_total",
        "tiktok_interaction_tasks_total",
        "tiktok_interaction_completed_total",
        "tiktok_interaction_failed_total",
        "tiktok_interaction_queue_total",
        "tiktok_interaction_latency_seconds",
    )

    def __init__(self) -> None:
        self.values = {name: 0.0 for name in self.NAMES}

    def increment(self, name: str, value: float = 1.0) -> None:
        if name not in self.values:
            raise KeyError(name)
        self.values[name] += value

    def set(self, name: str, value: float) -> None:
        if name not in self.values:
            raise KeyError(name)
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return (
            "\n".join(f"{name} {value}" for name, value in self.values.items()) + "\n"
        )
