"""Prometheus-compatible multi-agent metrics."""

from collections import defaultdict
from threading import Lock

METRICS = (
    "multi_agents_total",
    "agent_teams_total",
    "coordination_cycles_total",
    "delegations_total",
    "consensus_total",
    "multi_agent_latency_seconds",
    "multi_agent_failures_total",
)


class MultiAgentMetrics:
    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise KeyError(f"Unknown multi-agent metric: {name}")
        with self._lock:
            self._values[name] += amount

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} counter\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )


__all__ = ("METRICS", "MultiAgentMetrics")
