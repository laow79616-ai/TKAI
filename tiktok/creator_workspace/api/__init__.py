"""HTTP registration for the TikTok Creator Workspace."""

from __future__ import annotations

from typing import Any

from ..models import CreatorScope
from ..service import TikTokCreatorWorkspace

ROUTES = (
    "/tiktok/creator-workspace/projects",
    "/tiktok/creator-workspace/calendar",
    "/tiktok/creator-workspace/assets",
    "/tiktok/creator-workspace/reviews",
    "/tiktok/creator-workspace/approvals",
    "/tiktok/creator-workspace/analytics",
)


def _scope() -> CreatorScope:
    return CreatorScope(
        "default", "default", "api", frozenset({"tiktok:creator:admin"})
    )


def register_creator_workspace_routes(
    app: Any, service: TikTokCreatorWorkspace
) -> None:
    readers = {
        ROUTES[0]: lambda: service.list_projects(_scope()),
        ROUTES[1]: lambda: service.calendar(_scope()),
        ROUTES[2]: lambda: service.list_assets(_scope()),
        ROUTES[3]: lambda: service.reviews_for(_scope()),
        ROUTES[4]: lambda: service.approvals_for(_scope()),
        ROUTES[5]: lambda: service.analytics(_scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path,
            endpoint,
            methods=["GET"],
            tags=["tiktok-creator-workspace"],
        )
    app.add_api_route(
        "/tiktok/creator-workspace/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-creator-workspace"],
    )
    app.add_api_route(
        "/tiktok/creator-workspace/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-creator-workspace"],
    )
