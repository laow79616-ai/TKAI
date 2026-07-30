"""GET-only API for the V9 Adaptive Operations Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.operations_mesh.fabric import AdaptiveOperationsMesh

RESOURCES = (
    "profiles",
    "federation",
    "operations",
    "workflows",
    "capabilities",
    "services",
    "resources",
    "runtime",
    "readiness",
    "capacity",
    "dependencies",
    "constraints",
    "risks",
    "recovery",
    "continuity",
    "maintenance",
    "pause",
    "killswitch",
    "evaluations",
    "recommendations",
    "reviews",
    "approvals",
    "governance",
    "compatibility",
    "history",
    "analytics",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = tuple(f"/v9/operations/{resource}" for resource in RESOURCES)


def route_handlers(mesh: AdaptiveOperationsMesh) -> dict[str, Callable[[], object]]:
    def handler(name: str) -> object:
        value = mesh.snapshot()[name]
        return value if isinstance(value, dict) else {"items": value, "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def route(name: str = resource) -> object:
            return handler(name)

        handlers[f"/v9/operations/{resource}"] = route
    return handlers


def register_routes(
    app: Any, mesh: AdaptiveOperationsMesh | None = None
) -> AdaptiveOperationsMesh:
    selected = mesh or AdaptiveOperationsMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V9 Adaptive Operations Mesh"]
        )
    return selected


def create_router(mesh: AdaptiveOperationsMesh | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the router.") from error
    router = APIRouter()
    register_routes(router, mesh)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V9 Adaptive Operations Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Advisory operations metadata"}
                    },
                }
            }
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
