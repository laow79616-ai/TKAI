"""GET-only API integration for the internal service mesh."""

from __future__ import annotations

from typing import Any

from tkai.v7.service_mesh.contracts import serialize
from tkai.v7.service_mesh.framework import (
    GLOBAL_REGISTRY,
    ServiceRegistry,
    ServiceRouter,
)


def register_service_mesh_routes(
    app: Any, registry: ServiceRegistry | None = None
) -> None:
    selected = registry or GLOBAL_REGISTRY
    router = ServiceRouter(selected)

    def models() -> list[dict[str, object]]:
        return [serialize(model) for model in selected.snapshot()]

    routes: dict[str, Any] = {
        "catalog": lambda: {"items": models(), "total": len(selected.list())},
        "registry": lambda: {
            "items": models(),
            "indexes": ("category", "owner", "status", "interface"),
        },
        "routing": lambda: {"table": router.table()},
        "health": lambda: {
            "items": [
                {
                    "service_id": item.service_id,
                    "health": serialize(selected.health.check(item.service_id)),
                }
                for item in selected.list()
            ]
        },
        "metrics": lambda: {
            "items": [
                {
                    "service_id": item.service_id,
                    "metrics": serialize(selected.metrics.get(item.service_id)),
                }
                for item in selected.list()
            ]
        },
        "lifecycle": lambda: {
            "items": [
                {
                    "service_id": item.service_id,
                    "status": item.status.value,
                    "history": serialize(item.lifecycle),
                }
                for item in selected.list()
            ]
        },
        "dependencies": lambda: {"graph": selected.graph().as_dict()},
    }
    for resource, handler in routes.items():
        app.add_api_route(
            f"/v7/services/{resource}",
            handler,
            methods=["GET"],
            tags=["V7 Service Mesh"],
        )


__all__ = ("register_service_mesh_routes",)
