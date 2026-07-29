"""GET-only API for the TikTok Predictive Analytics Center."""

from __future__ import annotations

from typing import Any

from ..models import PredictiveContext
from ..service import TikTokPredictiveAnalyticsCenter

RESOURCE_NAMES = (
    "profiles",
    "forecasts",
    "trends",
    "scenarios",
    "capacity",
    "risk",
    "confidence",
    "recommendations",
)
ROUTES = tuple(f"/tiktok/predictive/{name}" for name in RESOURCE_NAMES) + (
    "/tiktok/predictive/history",
    "/tiktok/predictive/analytics",
)


def register_predictive_routes(
    app: Any, service: TikTokPredictiveAnalyticsCenter
) -> None:
    def context() -> PredictiveContext:
        return PredictiveContext(
            "default",
            "default",
            "api",
            frozenset({"tiktok:predictive:read"}),
        )

    for name in RESOURCE_NAMES:
        store = getattr(service, name)

        def endpoint(
            store: dict[str, object] = store,
        ) -> list[dict[str, object]]:
            return service.items(store, context())

        app.add_api_route(
            f"/tiktok/predictive/{name}",
            endpoint,
            methods=["GET"],
            tags=["tiktok-predictive"],
        )
    app.add_api_route(
        "/tiktok/predictive/history",
        lambda: service.get_history(context()),
        methods=["GET"],
        tags=["tiktok-predictive"],
    )
    app.add_api_route(
        "/tiktok/predictive/analytics",
        lambda: service.analytics(context()),
        methods=["GET"],
        tags=["tiktok-predictive"],
    )
    app.add_api_route(
        "/tiktok/predictive/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-predictive"],
    )
    app.add_api_route(
        "/tiktok/predictive/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-predictive"],
    )
