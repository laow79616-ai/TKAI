"""HTTP route registration for the TikTok AI Continuous Optimization Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RequestScope
from ..service import TikTokAIContinuousOptimizationCenter

RESOURCES = (
    "profiles",
    "objectives",
    "baselines",
    "signals",
    "candidates",
    "experiments",
    "simulations",
    "evaluations",
    "recommendations",
    "approvals",
    "changes",
    "rollbacks",
)
ROUTES = tuple(f"/tiktok/optimization-center/{name}" for name in RESOURCES) + (
    "/tiktok/optimization-center/history",
    "/tiktok/optimization-center/analytics",
)


def register_optimization_routes(
    app: Any, service: TikTokAIContinuousOptimizationCenter
) -> None:
    scope = RequestScope(
        "default", "default", "api", frozenset({"tiktok:optimization:admin"})
    )

    def serialize(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope)]

    for resource, path in zip(RESOURCES, ROUTES[: len(RESOURCES)], strict=True):
        app.add_api_route(
            path,
            lambda resource=resource: serialize(getattr(service, resource).values()),
            methods=["GET"],
            tags=["tiktok-optimization-center"],
        )
    app.add_api_route(
        ROUTES[-2],
        lambda: service.history(scope),
        methods=["GET"],
        tags=["tiktok-optimization-center"],
    )
    app.add_api_route(
        ROUTES[-1],
        lambda: service.analytics(scope),
        methods=["GET"],
        tags=["tiktok-optimization-center"],
    )
    app.add_api_route(
        "/tiktok/optimization-center/dashboard",
        lambda: service.dashboard(scope),
        methods=["GET"],
        tags=["tiktok-optimization-center"],
    )
    app.add_api_route(
        "/tiktok/optimization-center/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-optimization-center"],
    )
