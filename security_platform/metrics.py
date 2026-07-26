"""Prometheus-compatible metrics for the Enterprise AI Security Platform."""

from __future__ import annotations

from collections import defaultdict
from threading import Lock

METRICS = (
    "security_events_total",
    "auth_failures_total",
    "policy_denials_total",
    "incident_total",
    "secret_rotations_total",
    "active_sessions_total",
)


class SecurityMetrics:
    """Thread-safe, dependency-free security counters and gauges."""

    def __init__(self) -> None:
        self._values: dict[str, float] = defaultdict(float)
        self._lock = Lock()
        for name in METRICS:
            self._values[name] = 0

    def increment(self, name: str, amount: float = 1) -> None:
        with self._lock:
            self._values[name] += amount

    def set(self, name: str, value: float) -> None:
        with self._lock:
            self._values[name] = value

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            return dict(self._values)

    def render_prometheus(self) -> str:
        return "".join(
            f"# TYPE {name} gauge\n{name} {value:g}\n"
            for name, value in sorted(self.snapshot().items())
        )


__all__ = ("METRICS", "SecurityMetrics")
