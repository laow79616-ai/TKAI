"""GET-only API adapter for the TKAI V10 Sovereign Trust Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.trust_mesh import SovereignTrustMesh

RESOURCES = (
    "profiles",
    "domains",
    "identities",
    "relationships",
    "integrity",
    "attestations",
    "scores",
    "compatibility",
    "health",
    "metrics",
)
GET_ROUTES = tuple(f"/v10/trust/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignTrustMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "automatic_trust": False,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/trust/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignTrustMesh | None = None
) -> SovereignTrustMesh:
    selected = mesh or SovereignTrustMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Trust Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Trust Mesh"])(handler)
    return selected


def create_router(mesh: SovereignTrustMesh | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the trust router.") from error
    router = APIRouter()
    register_routes(router, mesh)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Trust Mesh"]}} for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "RESOURCES",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
