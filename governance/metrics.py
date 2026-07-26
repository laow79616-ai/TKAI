"""Prometheus-compatible governance metrics."""

METRICS = (
    "governance_policies_total",
    "governance_active_policies",
    "governance_risks_total",
    "governance_high_risks_total",
    "governance_findings_total",
    "governance_approvals_total",
    "governance_incidents_total",
    "governance_exceptions_total",
)


class GovernanceMetrics:
    def __init__(self) -> None:
        self.values: dict[str, float] = {name: 0 for name in METRICS}

    def increment(self, name: str, amount: float = 1) -> None:
        if name not in self.values:
            raise ValueError("Unknown governance metric.")
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        if name not in self.values:
            raise ValueError("Unknown governance metric.")
        self.values[name] = value

    def snapshot(self) -> dict[str, float]:
        return dict(self.values)

    def render_prometheus(self) -> str:
        return "".join(f"{name} {value}\n" for name, value in self.values.items())
