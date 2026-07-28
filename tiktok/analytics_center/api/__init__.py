"""HTTP routes for the TikTok AI Analytics Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import AnalyticsScope
from ..service import TikTokAIAnalyticsCenter

ROUTES = tuple(
    f"/tiktok/analytics/{name}"
    for name in (
        "reports",
        "kpis",
        "trends",
        "forecast",
        "history",
        "insights",
        "exports",
    )
)


def register_analytics_center_routes(
    app: Any, service: TikTokAIAnalyticsCenter
) -> None:
    def scope() -> AnalyticsScope:
        return AnalyticsScope(
            "default", "default", "api", frozenset({"tiktok:analytics:admin"})
        )

    stores = (
        service.reports,
        service.kpis,
        service.trends,
        service.forecasts,
        service.history,
        service.insights,
        service.exports,
    )
    for path, store in zip(ROUTES, stores, strict=True):
        app.add_api_route(
            path,
            lambda values=store: [
                asdict(item) for item in service.scoped_values(values.values(), scope())
            ],
            methods=["GET"],
            tags=["tiktok-ai-analytics-center"],
        )
    app.add_api_route(
        "/tiktok/analytics/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-ai-analytics-center"],
    )
    app.add_api_route(
        "/tiktok/analytics/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-ai-analytics-center"],
    )
