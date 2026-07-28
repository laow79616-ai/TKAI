"""Transport-neutral API registration for the TikTok Resource Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import ResourceScope
from ..service import TikTokResourceCenter

RESOURCE_NAMES = (
    "resources",
    "inventory",
    "allocations",
    "reservations",
    "leases",
    "capacity",
    "utilization",
    "health",
    "statistics",
)
ROUTES = tuple(f"/tiktok/resource-center/{name}" for name in RESOURCE_NAMES)


def register_resource_center_routes(app: Any, service: TikTokResourceCenter) -> None:
    def scope() -> ResourceScope:
        return ResourceScope(
            "default", "default", "api", frozenset({"tiktok:resources:admin"})
        )

    def values(store: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(store.values(), scope())]

    handlers = {
        "resources": lambda: values(service.resources),
        "inventory": lambda: {
            "resources": values(service.resources),
            "size": len(service.scoped_values(service.resources.values(), scope())),
        },
        "allocations": lambda: values(service.allocations),
        "reservations": lambda: values(service.reservations),
        "leases": lambda: values(service.leases),
        "capacity": lambda: service.capacity(scope()),
        "utilization": lambda: service.utilization(scope()),
        "health": lambda: service.health(scope()),
        "statistics": lambda: service.statistics(scope()),
    }
    for name, path in zip(RESOURCE_NAMES, ROUTES, strict=True):
        app.add_api_route(
            path, handlers[name], methods=["GET"], tags=["tiktok-resource-center"]
        )
    app.add_api_route(
        "/tiktok/resource-center/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-resource-center"],
    )
    app.add_api_route(
        "/tiktok/resource-center/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-resource-center"],
    )
