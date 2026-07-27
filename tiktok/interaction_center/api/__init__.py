"""HTTP registration for the TikTok AI Interaction Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import InteractionScope
from ..service import TikTokInteractionCenter

ROUTES = (
    "/tiktok/interaction/projects",
    "/tiktok/interaction/tasks",
    "/tiktok/interaction/drafts",
    "/tiktok/interaction/templates",
    "/tiktok/interaction/reviews",
    "/tiktok/interaction/analytics",
)


def _scope() -> InteractionScope:
    return InteractionScope(
        "default", "default", "api", frozenset({"tiktok:interaction:admin"})
    )


def register_interaction_routes(app: Any, service: TikTokInteractionCenter) -> None:
    scope = _scope
    readers = {
        ROUTES[0]: lambda: [p.to_dict() for p in service.list_projects(scope())],
        ROUTES[1]: lambda: [
            asdict(v)
            for v in service.tasks.values()
            if v.tenant == scope().tenant and v.workspace == scope().workspace
        ],
        ROUTES[2]: lambda: [
            asdict(v)
            for v in service.drafts.values()
            if v.tenant == scope().tenant and v.workspace == scope().workspace
        ],
        ROUTES[3]: lambda: [
            asdict(v)
            for v in service.templates.values()
            if v.tenant == scope().tenant and v.workspace == scope().workspace
        ],
        ROUTES[4]: lambda: [
            asdict(v)
            for v in service.reviews.values()
            if v.tenant == scope().tenant and v.workspace == scope().workspace
        ],
        ROUTES[5]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-interaction"])
    app.add_api_route(
        "/tiktok/interaction/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-interaction"],
    )
    app.add_api_route(
        "/tiktok/interaction/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-interaction"],
    )
