"""HTTP registration for the TikTok Data Collection Center."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from ..models import DataScope
from ..service import TikTokDataCollectionCenter

ROUTES = (
    "/tiktok/data/projects",
    "/tiktok/data/jobs",
    "/tiktok/data/datasets",
    "/tiktok/data/pipelines",
    "/tiktok/data/history",
    "/tiktok/data/analytics",
)


def _scope() -> DataScope:
    return DataScope("default", "default", "api", frozenset({"tiktok:data:admin"}))


def _scoped_values(values: Any) -> list[Any]:
    scope = _scope()
    return [
        value
        for value in values
        if value.tenant == scope.tenant and value.workspace == scope.workspace
    ]


def register_data_collection_routes(
    app: Any, service: TikTokDataCollectionCenter
) -> None:
    readers: dict[str, Callable[[], Any]] = {
        ROUTES[0]: lambda: [item.to_dict() for item in service.list_projects(_scope())],
        ROUTES[1]: lambda: [
            asdict(item) for item in _scoped_values(service.jobs.values())
        ],
        ROUTES[2]: lambda: [
            asdict(item) for item in _scoped_values(service.datasets.values())
        ],
        ROUTES[3]: lambda: [
            asdict(item) for item in _scoped_values(service.pipelines.values())
        ],
        ROUTES[4]: lambda: [asdict(item) for item in _scoped_values(service.history)],
        ROUTES[5]: lambda: service.analytics(_scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-data"])
    app.add_api_route(
        "/tiktok/data/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-data"],
    )
    app.add_api_route(
        "/tiktok/data/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-data"],
    )
