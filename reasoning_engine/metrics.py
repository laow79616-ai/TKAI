"""Prometheus-compatible reasoning engine metrics."""

from __future__ import annotations

METRICS = (
    "reasoning_sessions_total",
    "reasoning_plans_total",
    "reasoning_decisions_total",
    "reasoning_validation_failures_total",
    "reasoning_duration_seconds",
    "reasoning_simulations_total",
)


class ReasoningMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown reasoning metric.")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in self.values:
            raise ValueError("Unknown reasoning metric.")
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
