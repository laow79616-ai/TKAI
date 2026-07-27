"""Prometheus-compatible Decision Intelligence metrics."""

from collections import defaultdict
from threading import Lock

COUNTERS = (
    "decisions_total",
    "decision_evaluations_total",
    "decision_recommendations_total",
    "decision_approvals_total",
    "decision_simulations_total",
    "decision_execution_success_total",
)
HISTOGRAMS = ("decision_latency_seconds",)
METRICS = COUNTERS + HISTOGRAMS


class DecisionMetrics:
    """Thread-safe metric registry for the reference control plane."""

    def __init__(self) -> None:
        self._values = {name: 0.0 for name in METRICS}
        self._counts: dict[str, int] = defaultdict(int)
        self._lock = Lock()

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in COUNTERS:
            raise KeyError(f"Unknown decision counter: {name}")
        with self._lock:
            self._values[name] += amount

    def observe(self, name: str, value: float) -> None:
        if name not in HISTOGRAMS:
            raise KeyError(f"Unknown decision histogram: {name}")
        if value < 0:
            raise ValueError("Metric observations cannot be negative.")
        with self._lock:
            self._values[name] += value
            self._counts[name] += 1

    def snapshot(self) -> dict[str, float]:
        with self._lock:
            result = dict(self._values)
            for name in HISTOGRAMS:
                result[f"{name}_count"] = float(self._counts[name])
            return result

    def render_prometheus(self) -> str:
        snapshot = self.snapshot()
        lines: list[str] = []
        for name in COUNTERS:
            lines.extend((f"# TYPE {name} counter", f"{name} {snapshot[name]:g}"))
        for name in HISTOGRAMS:
            lines.extend(
                (
                    f"# TYPE {name} summary",
                    f"{name}_sum {snapshot[name]:g}",
                    f"{name}_count {snapshot[f'{name}_count']:g}",
                )
            )
        return "\n".join(lines) + "\n"
