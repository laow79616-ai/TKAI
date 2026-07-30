"""GET-only API for the V9 Adaptive Recovery Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.recovery_mesh.fabric import AdaptiveRecoveryMesh

RESOURCES = (
    "profiles",
    "federation",
    "incidents",
    "failures",
    "impact",
    "readiness",
    "resilience",
    "continuity",
    "recovery",
    "rollback",
    "snapshots",
    "checkpoints",
    "restoration",
    "degraded",
    "capacity",
    "dependencies",
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
GET_ROUTES = tuple(f"/v9/recovery/{resource}" for resource in RESOURCES)


def route_handlers(mesh: AdaptiveRecoveryMesh) -> dict[str, Callable[[], object]]:
    def handler(name: str) -> object:
        value = mesh.snapshot()[name]
        return value if isinstance(value, dict) else {"items": value, "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def route(name: str = resource) -> object:
            return handler(name)

        handlers[f"/v9/recovery/{resource}"] = route
    return handlers


def register_routes(
    app: Any, mesh: AdaptiveRecoveryMesh | None = None
) -> AdaptiveRecoveryMesh:
    selected = mesh or AdaptiveRecoveryMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V9 Adaptive Recovery Mesh"]
        )
    return selected


def create_router(mesh: AdaptiveRecoveryMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Recovery Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {"200": {"description": "Advisory recovery metadata"}},
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
