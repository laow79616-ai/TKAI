"""Prometheus-compatible orchestrator metrics."""

METRICS = (
    "execution_plans_total",
    "execution_total",
    "execution_failed_total",
    "execution_retry_total",
    "queue_depth",
    "checkpoint_total",
    "recovery_total",
)


class OrchestratorMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown orchestrator metric.")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in self.values:
            raise ValueError("Unknown orchestrator metric.")
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
