"""Prometheus-compatible workflow metrics."""

METRICS = (
    "workflow_total",
    "workflow_runs_total",
    "workflow_success_total",
    "workflow_failed_total",
    "workflow_duration_seconds",
    "approval_total",
    "approval_timeout_total",
)


class WorkflowMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in METRICS:
            raise ValueError("Unknown workflow metric.")
        self.values[name] = self.values[name] + amount

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
