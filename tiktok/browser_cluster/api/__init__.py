"""Declarative Browser Cluster API bindings."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..models import ClusterScope
from ..service import TikTokBrowserCluster

BASE = "/tiktok/browser-cluster"
ROUTES = tuple(
    [BASE]
    + [
        f"{BASE}/{resource}"
        for resource in (
            "nodes",
            "instances",
            "resources",
            "queues",
            "health",
            "recovery",
            "statistics",
        )
    ]
)


def register_browser_cluster_routes(app: Any, cluster: TikTokBrowserCluster) -> None:
    def scoped(tenant: str, workspace: str, actor: str) -> ClusterScope:
        return ClusterScope(tenant, workspace, actor)

    def section(name: str) -> Callable[..., Any]:
        return lambda tenant, workspace, actor: cluster.dashboard(
            scoped(tenant, workspace, actor)
        )[name]

    handlers: dict[str, Callable[..., Any]] = {
        BASE: lambda tenant, workspace, actor: cluster.dashboard(
            scoped(tenant, workspace, actor)
        ),
        f"{BASE}/nodes": section("nodes"),
        f"{BASE}/instances": section("instances"),
        f"{BASE}/resources": section("resources"),
        f"{BASE}/queues": section("queues"),
        f"{BASE}/health": lambda tenant, workspace, actor: cluster.health(
            scoped(tenant, workspace, actor)
        ),
        f"{BASE}/recovery": section("recovery"),
        f"{BASE}/statistics": lambda tenant, workspace, actor: cluster.statistics(
            scoped(tenant, workspace, actor)
        ),
    }
    for path, handler in handlers.items():
        try:
            app.add_api_route(
                path, handler, methods=["GET"], tags=["tiktok-browser-cluster"]
            )
        except TypeError:
            app.add_api_route(path, handler, methods=["GET"])
