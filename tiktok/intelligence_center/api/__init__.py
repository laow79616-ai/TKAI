"""HTTP API for the TikTok Autonomous Intelligence Center."""

from __future__ import annotations

from typing import Any

from ..models import IntelligenceContext
from ..service import TikTokAutonomousIntelligenceCenter

ROUTES = (
    "/tiktok/intelligence/profiles",
    "/tiktok/intelligence/reasoning",
    "/tiktok/intelligence/recommendations",
    "/tiktok/intelligence/predictions",
    "/tiktok/intelligence/analytics",
)


def register_intelligence_routes(
    app: Any, service: TikTokAutonomousIntelligenceCenter
) -> None:
    def context() -> IntelligenceContext:
        return IntelligenceContext(
            "default",
            "default",
            "api",
            frozenset({"tiktok:intelligence:admin"}),
        )

    app.add_api_route(
        ROUTES[0],
        lambda: service._items(service.profiles, context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        ROUTES[1],
        lambda: service._items(service.reasoning_results, context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        ROUTES[2],
        lambda: service._items(service.recommendations, context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        ROUTES[3],
        lambda: service._items(service.predictions, context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        ROUTES[4],
        lambda: service.analytics(context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        "/tiktok/intelligence/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
    app.add_api_route(
        "/tiktok/intelligence/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-intelligence"],
    )
