"""Read-only HTTP API for the TikTok Knowledge Evolution Center."""

from __future__ import annotations

from typing import Any

from ..models import KnowledgeContext
from ..service import TikTokKnowledgeEvolutionCenter

ROUTES = (
    "/tiktok/knowledge/profiles",
    "/tiktok/knowledge/evolution",
    "/tiktok/knowledge/versions",
    "/tiktok/knowledge/recommendations",
    "/tiktok/knowledge/analytics",
)


def register_knowledge_evolution_routes(
    app: Any, service: TikTokKnowledgeEvolutionCenter
) -> None:
    def context() -> KnowledgeContext:
        return KnowledgeContext(
            "default",
            "default",
            "api",
            frozenset({"tiktok:knowledge:read"}),
        )

    endpoints = (
        lambda: service._items(service.profiles, context()),
        lambda: service.evolution(context()),
        lambda: service._items(service.versions, context()),
        lambda: service._items(service.recommendations, context()),
        lambda: service.analytics(context()),
    )
    for path, endpoint in zip(ROUTES, endpoints, strict=True):
        app.add_api_route(
            path,
            endpoint,
            methods=["GET"],
            tags=["tiktok-knowledge"],
        )
    app.add_api_route(
        "/tiktok/knowledge/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-knowledge"],
    )
    app.add_api_route(
        "/tiktok/knowledge/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-knowledge"],
    )
