"""Dependency-free CRM Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_crm_records_total",
    "tiktok_crm_contacts_total",
    "tiktok_crm_opportunities_total",
    "tiktok_crm_followups_total",
    "tiktok_crm_conversion_rate",
    "tiktok_crm_latency_seconds",
)


class CRMMetrics:
    def __init__(self) -> None:
        self.values: defaultdict[str, float] = defaultdict(float)
        for name in METRIC_NAMES:
            self.values[name] = 0.0

    def increment(self, name: str, amount: float = 1.0) -> None:
        self.values[name] += amount

    def set(self, name: str, value: float) -> None:
        self.values[name] = value

    def render_prometheus(self) -> str:
        return "\n".join(f"{name} {self.values[name]}" for name in METRIC_NAMES) + "\n"
