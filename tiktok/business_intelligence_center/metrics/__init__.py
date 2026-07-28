"""Prometheus-style metrics for TikTok Business Intelligence."""

from collections import defaultdict

METRIC_NAMES = (
    "tiktok_business_intelligence_workspaces_total",
    "tiktok_business_intelligence_datasets_total",
    "tiktok_business_intelligence_kpis_total",
    "tiktok_business_intelligence_queries_total",
    "tiktok_business_intelligence_reports_total",
    "tiktok_business_intelligence_dashboards_total",
    "tiktok_business_intelligence_forecasts_total",
    "tiktok_business_intelligence_insights_total",
    "tiktok_business_intelligence_exports_total",
    "tiktok_business_intelligence_query_seconds",
    "tiktok_business_intelligence_analysis_seconds",
    "tiktok_business_intelligence_data_freshness_seconds",
)


class BusinessIntelligenceMetrics:
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
