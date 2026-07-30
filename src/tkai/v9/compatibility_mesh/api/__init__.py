"""GET-only API for the V9 Adaptive Compatibility Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.compatibility_mesh.fabric import AdaptiveCompatibilityMesh

RESOURCES = (
    "profiles",
    "federation",
    "components",
    "versions",
    "capabilities",
    "configurations",
    "schemas",
    "storage",
    "plugins",
    "deployments",
    "migrations",
    "upgrades",
    "rollback",
    "assessments",
    "matrices",
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
GET_ROUTES = tuple(f"/v9/compatibility/{resource}" for resource in RESOURCES)


def route_handlers(
    mesh: AdaptiveCompatibilityMesh,
) -> dict[str, Callable[[], object]]:
    def handler(name: str) -> object:
        value = mesh.snapshot()[name]
        return value if isinstance(value, dict) else {"items": value, "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def route(name: str = resource) -> object:
            return handler(name)

        handlers[f"/v9/compatibility/{resource}"] = route
    return handlers


def register_routes(
    app: Any, mesh: AdaptiveCompatibilityMesh | None = None
) -> AdaptiveCompatibilityMesh:
    selected = mesh or AdaptiveCompatibilityMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V9 Adaptive Compatibility Mesh"]
        )
    return selected


def create_router(mesh: AdaptiveCompatibilityMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Compatibility Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Advisory compatibility metadata"}
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
