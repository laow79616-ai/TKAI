"""HTTP route registration for the TikTok AI Growth Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RequestScope
from ..service import TikTokAIGrowthCenter

RESOURCES = ("profiles", "goals", "kpis", "trends", "recommendations")
ROUTES = tuple(f"/tiktok/growth/{name}" for name in RESOURCES) + (
    "/tiktok/growth/analytics",
)


def register_growth_routes(app: Any, service: TikTokAIGrowthCenter) -> None:
    scope = RequestScope(
        "default", "default", "api", frozenset({"tiktok:growth:admin"})
    )

    def serialize(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope)]

    for resource, path in zip(RESOURCES, ROUTES[: len(RESOURCES)], strict=True):
        app.add_api_route(
            path,
            lambda resource=resource: serialize(getattr(service, resource).values()),
            methods=["GET"],
            tags=["tiktok-growth-center"],
        )
    app.add_api_route(
        ROUTES[-1],
        lambda: service.analytics(scope),
        methods=["GET"],
        tags=["tiktok-growth-center"],
    )
    app.add_api_route(
        "/tiktok/growth/dashboard",
        lambda: service.dashboard(scope),
        methods=["GET"],
        tags=["tiktok-growth-center"],
    )
    app.add_api_route(
        "/tiktok/growth/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-growth-center"],
    )
