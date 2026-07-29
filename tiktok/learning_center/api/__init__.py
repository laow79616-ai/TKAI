"""GET-only API for the TikTok Autonomous Learning Center."""

from __future__ import annotations

from typing import Any

from ..models import LearningContext
from ..service import TikTokAutonomousLearningCenter

ROUTES = (
    "/tiktok/learning/profiles",
    "/tiktok/learning/patterns",
    "/tiktok/learning/recommendations",
    "/tiktok/learning/analytics",
)


def register_learning_routes(
    app: Any, service: TikTokAutonomousLearningCenter
) -> None:
    def context() -> LearningContext:
        return LearningContext(
            "default",
            "default",
            "api",
            frozenset({"tiktok:learning:read"}),
        )

    endpoints = (
        lambda: service._items(service.profiles, context()),
        lambda: service._items(service.patterns, context()),
        lambda: service._items(service.recommendations, context()),
        lambda: service.analytics(context()),
    )
    for route, endpoint in zip(ROUTES, endpoints, strict=True):
        app.add_api_route(
            route, endpoint, methods=["GET"], tags=["tiktok-learning"]
        )
    app.add_api_route(
        "/tiktok/learning/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-learning"],
    )
    app.add_api_route(
        "/tiktok/learning/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-learning"],
    )
