"""GET-only API adapter for the Sovereign Knowledge Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.knowledge_mesh import SovereignKnowledgeMesh

RESOURCES = (
    "profiles",
    "domains",
    "concepts",
    "entities",
    "relationships",
    "evidence",
    "provenance",
    "lineage",
    "health",
    "metrics",
)
GET_ROUTES = tuple(f"/v10/knowledge/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignKnowledgeMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "automatic_ingestion": False,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/knowledge/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignKnowledgeMesh | None = None
) -> SovereignKnowledgeMesh:
    selected = mesh or SovereignKnowledgeMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Knowledge Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Knowledge Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Knowledge Mesh"]}}
            for path in GET_ROUTES
        },
    }


__all__ = ("GET_ROUTES", "RESOURCES", "openapi_contract", "register_routes")
