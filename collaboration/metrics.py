"""Prometheus-compatible collaboration metrics."""

METRICS = (
    "workspaces_total",
    "projects_total",
    "collaboration_sessions_total",
    "tasks_total",
    "handoffs_total",
    "messages_total",
    "notifications_total",
)


class CollaborationMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown collaboration metric.")
        self.values[name] += amount

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
