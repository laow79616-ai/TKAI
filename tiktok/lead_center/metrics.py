"""Dependency-free Lead Management Center metrics."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_leads_total",
    "tiktok_leads_new_total",
    "tiktok_leads_qualified_total",
    "tiktok_leads_unqualified_total",
    "tiktok_leads_assigned_total",
    "tiktok_leads_followups_due_total",
    "tiktok_leads_converted_total",
    "tiktok_leads_imports_total",
    "tiktok_leads_duplicates_total",
    "tiktok_leads_consent_withdrawals_total",
    "tiktok_lead_qualification_seconds",
    "tiktok_lead_assignment_seconds",
)


class LeadMetrics:
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
