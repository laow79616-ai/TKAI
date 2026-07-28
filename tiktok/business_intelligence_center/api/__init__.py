"""FastAPI routes for TikTok Business Intelligence."""

from __future__ import annotations

from typing import Any

from ..models import (
    BIScope,
    BIWorkspace,
    Dataset,
    Insight,
    Metric,
    Query,
    SemanticModel,
    WorkspaceStatus,
)
from ..service import TikTokBusinessIntelligenceCenter

ROUTES = tuple(
    f"/tiktok/business-intelligence/{name}"
    for name in (
        "workspaces",
        "datasets",
        "semantic-models",
        "kpis",
        "metrics",
        "queries",
        "dashboards",
        "reports",
        "comparisons",
        "trends",
        "forecasts",
        "insights",
        "snapshots",
        "exports",
        "history",
        "governance",
        "analytics",
    )
)
TAG = ["tiktok-business-intelligence"]


def _scope() -> BIScope:
    return BIScope(
        "default", "default", "api", frozenset({"tiktok:business-intelligence:admin"})
    )


def register_business_intelligence_routes(
    app: Any, service: TikTokBusinessIntelligenceCenter
) -> None:
    def values(collection: Any) -> Any:
        def read() -> list[Any]:
            return service.scoped_values(collection.values(), _scope())

        return read

    app.add_api_route(ROUTES[0], values(service.workspaces), methods=["GET"], tags=TAG)
    app.add_api_route(
        ROUTES[0],
        lambda item: service.create_workspace(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{identifier}}/transition",
        lambda identifier, status: service.transition(identifier, status, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(ROUTES[1], values(service.datasets), methods=["GET"], tags=TAG)
    app.add_api_route(
        ROUTES[1],
        lambda item: service.register_dataset(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[2], values(service.semantic_models), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[2],
        lambda item: service.register_semantic_model(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[3], lambda: list(service.kpis.values()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[4], values(service.metric_definitions), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[4],
        lambda item: service.register_metric(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[5],
        lambda item: service.execute_query(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    collections = (
        service.dashboards,
        service.reports,
        service.comparisons,
        service.trends,
        service.forecasts,
        service.insights,
        service.snapshots,
        service.exports,
    )
    for path, collection in zip(ROUTES[6:14], collections, strict=True):
        app.add_api_route(path, values(collection), methods=["GET"], tags=TAG)
    for path, kind in zip(
        ROUTES[6:11],
        ("dashboard", "report", "comparison", "trend", "forecast"),
        strict=True,
    ):
        app.add_api_route(
            path,
            lambda request, kind=kind: service.create_artifact(
                kind, str(request["id"]), dict(request.get("payload", {})), _scope()
            ),
            methods=["POST"],
            tags=TAG,
        )
    app.add_api_route(
        ROUTES[11],
        lambda item: service.add_insight(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[14], lambda: service.history(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[15], values(service.governance_records), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[16], lambda: service.analytics(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/business-intelligence/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/business-intelligence/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=TAG,
    )


API_MODELS = (
    BIWorkspace,
    Dataset,
    Insight,
    Metric,
    Query,
    SemanticModel,
    WorkspaceStatus,
)
