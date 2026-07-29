"""Read-only HTTP API for TikTok Performance Insights."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RequestScope
from ..service import TikTokPerformanceInsightsCenter

RESOURCES = (
    "profiles",
    "datasets",
    "metrics",
    "benchmarks",
    "comparisons",
    "trends",
    "anomalies",
    "forecasts",
    "insights",
    "recommendations",
    "reports",
    "snapshots",
    "history",
    "analytics",
)
ROUTES = tuple(f"/tiktok/performance-insights/{name}" for name in RESOURCES)


def register_performance_insights_routes(
    app: Any, service: TikTokPerformanceInsightsCenter
) -> None:
    scope = RequestScope(
        "default", "default", "api", frozenset({"tiktok:performance:admin"})
    )
    stores: dict[str, Any] = {
        "profiles": service.profiles,
        "datasets": service.datasets,
        "metrics": service.metrics_evaluated,
        "benchmarks": service.benchmarks,
        "comparisons": service.comparisons,
        "trends": service.trends,
        "anomalies": service.anomalies,
        "forecasts": service.forecasts,
        "insights": service.insights,
        "recommendations": service.recommendations,
        "reports": service.reports,
        "snapshots": service.snapshots,
    }

    def serialize(resource: str) -> list[dict[str, Any]]:
        return [
            asdict(item)
            for item in service.scoped_values(stores[resource].values(), scope)
        ]

    for resource in RESOURCES[:12]:
        app.add_api_route(
            f"/tiktok/performance-insights/{resource}",
            lambda resource=resource: serialize(resource),
            methods=["GET"],
            tags=["tiktok-performance-insights"],
        )
    app.add_api_route(
        ROUTES[12],
        lambda: service.history(scope),
        methods=["GET"],
        tags=["tiktok-performance-insights"],
    )
    app.add_api_route(
        ROUTES[13],
        lambda: service.analytics(scope),
        methods=["GET"],
        tags=["tiktok-performance-insights"],
    )
    app.add_api_route(
        "/tiktok/performance-insights/dashboard",
        lambda: service.dashboard(scope),
        methods=["GET"],
        tags=["tiktok-performance-insights"],
    )
    app.add_api_route(
        "/tiktok/performance-insights/metrics-exposure",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-performance-insights"],
    )
