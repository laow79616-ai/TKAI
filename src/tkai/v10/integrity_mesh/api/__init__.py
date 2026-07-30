"""GET-only API adapter for the Sovereign Integrity Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.integrity_mesh import SovereignIntegrityMesh

RESOURCES = (
    "profiles",
    "subjects",
    "evidence",
    "verification",
    "dependencies",
    "compatibility",
    "releases",
    "health",
    "metrics",
    "audit",
)
GET_ROUTES = tuple(f"/v10/integrity/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignIntegrityMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        if resource == "audit":
            return {"items": mesh.audit(), "read_only": True}
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "automatic_repair": False,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/integrity/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignIntegrityMesh | None = None
) -> SovereignIntegrityMesh:
    selected = mesh or SovereignIntegrityMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Integrity Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Integrity Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Integrity Mesh"]}}
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "RESOURCES",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
