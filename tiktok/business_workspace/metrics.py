"""Dependency-free metrics for the TikTok Business Workspace."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_business_workspaces_total",
    "tiktok_business_projects_total",
    "tiktok_business_operations_total",
    "tiktok_business_campaigns_total",
    "tiktok_business_approvals_total",
    "tiktok_business_latency_seconds",
)


class BusinessMetrics:
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
