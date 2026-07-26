"""Agent runtime metrics and Prometheus exposition."""

from __future__ import annotations

from collections import Counter
from threading import RLock

COUNTERS = (
    "agent_runs_total",
    "agent_success_total",
    "agent_failed_total",
    "agent_cancelled_total",
    "tool_calls_total",
    "tool_failures_total",
)


class AgentMetrics:
    def __init__(self) -> None:
        self._counters: Counter[str] = Counter()
        self._durations: list[float] = []
        self._lock = RLock()

    def increment(self, name: str, amount: int = 1) -> None:
        if name not in COUNTERS:
            raise ValueError(f"Unknown agent metric: {name}")
        with self._lock:
            self._counters[name] += amount

    def observe_duration(self, seconds: float) -> None:
        if seconds < 0:
            raise ValueError("Duration cannot be negative.")
        with self._lock:
            self._durations.append(seconds)

    def snapshot(self) -> dict[str, int | tuple[float, ...]]:
        with self._lock:
            return {
                **{name: self._counters[name] for name in COUNTERS},
                "agent_duration_seconds": tuple(self._durations),
            }

    def render_prometheus(self) -> str:
        snapshot = self.snapshot()
        lines: list[str] = []
        for name in COUNTERS:
            lines.extend(
                (f"# TYPE {name} counter", f"{name} {snapshot[name]}")
            )
        durations = snapshot["agent_duration_seconds"]
        assert isinstance(durations, tuple)
        lines.extend(
            (
                "# TYPE agent_duration_seconds summary",
                f"agent_duration_seconds_count {len(durations)}",
                f"agent_duration_seconds_sum {sum(durations):.6f}",
            )
        )
        return "\n".join(lines) + "\n"

