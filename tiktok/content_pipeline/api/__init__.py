"""HTTP routes for the Enterprise TikTok Content Pipeline."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RequestScope
from ..service import TikTokContentPipeline

RESOURCES = (
    "pipelines",
    "stages",
    "jobs",
    "inputs",
    "validation",
    "quality",
    "reviews",
    "approvals",
    "packages",
    "handoffs",
    "checkpoints",
    "recovery",
)
ROUTES = tuple(f"/tiktok/content-pipeline/{name}" for name in RESOURCES) + (
    "/tiktok/content-pipeline/history",
    "/tiktok/content-pipeline/analytics",
)


def register_content_pipeline_routes(app: Any, service: TikTokContentPipeline) -> None:
    scope = RequestScope(
        "default", "default", "api", frozenset({"tiktok:content-pipeline:admin"})
    )

    def serialize(resource: str) -> Any:
        values = getattr(service, resource)
        if resource == "history":
            return service.history(scope)
        if resource == "analytics":
            return service.analytics(scope)
        if isinstance(values, dict):
            result = []
            for item in values.values():
                tenant = getattr(
                    item,
                    "tenant",
                    item.get("tenant") if isinstance(item, dict) else None,
                )
                workspace = getattr(
                    item,
                    "workspace",
                    item.get("workspace") if isinstance(item, dict) else None,
                )
                if tenant == scope.tenant and workspace == scope.workspace:
                    result.append(
                        asdict(item) if hasattr(item, "__dataclass_fields__") else item
                    )
            return result
        return values

    for resource, path in zip(RESOURCES, ROUTES[: len(RESOURCES)], strict=True):
        app.add_api_route(
            path,
            lambda resource=resource: serialize(resource),
            methods=["GET"],
            tags=["tiktok-content-pipeline"],
        )
    app.add_api_route(
        ROUTES[-2],
        lambda: service.history(scope),
        methods=["GET"],
        tags=["tiktok-content-pipeline"],
    )
    app.add_api_route(
        ROUTES[-1],
        lambda: service.analytics(scope),
        methods=["GET"],
        tags=["tiktok-content-pipeline"],
    )
    app.add_api_route(
        "/tiktok/content-pipeline/dashboard",
        lambda: service.dashboard(scope),
        methods=["GET"],
        tags=["tiktok-content-pipeline"],
    )
    app.add_api_route(
        "/tiktok/content-pipeline/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-content-pipeline"],
    )
