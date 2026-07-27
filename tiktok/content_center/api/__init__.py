"""HTTP registration for the TikTok AI Content Center."""

from __future__ import annotations

from typing import Any

from ..models import ContentScope
from ..service import TikTokContentCenter

ROUTES = (
    "/tiktok/content/projects",
    "/tiktok/content/media",
    "/tiktok/content/drafts",
    "/tiktok/content/uploads",
    "/tiktok/content/publishing",
    "/tiktok/content/schedules",
    "/tiktok/content/templates",
    "/tiktok/content/analytics",
)


def _scope() -> ContentScope:
    return ContentScope(
        "default", "default", "api", frozenset({"tiktok:content:admin"})
    )


def register_content_center_routes(app: Any, service: TikTokContentCenter) -> None:
    readers = {
        ROUTES[0]: lambda: [item.to_dict() for item in service.list_projects(_scope())],
        ROUTES[1]: lambda: list(service.media.values()),
        ROUTES[2]: lambda: list(service.drafts.values()),
        ROUTES[3]: lambda: list(service.media.values()),
        ROUTES[4]: lambda: list(service.queue.values()),
        ROUTES[5]: lambda: list(service.schedules.values()),
        ROUTES[6]: lambda: list(service.templates.values()),
        ROUTES[7]: lambda: service.analytics(_scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-content"])
    app.add_api_route(
        "/tiktok/content/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-content"],
    )
    app.add_api_route(
        "/tiktok/content/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-content"],
    )
