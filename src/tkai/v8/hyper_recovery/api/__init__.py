"""GET-only API projections for V8 recovery metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_recovery.fabric import HyperRecoveryFabric

PROJECTIONS = (
    "profiles",
    "incidents",
    "failures",
    "impact",
    "readiness",
    "resilience",
    "continuity",
    "plans",
    "steps",
    "rollback",
    "snapshots",
    "checkpoints",
    "restoration",
    "degraded",
    "dependencies",
    "resources",
    "capacity",
    "validation",
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
GET_ROUTES = tuple(f"/v8/recovery/{name}" for name in PROJECTIONS)


def route_handlers(fabric: HyperRecoveryFabric) -> dict[str, Callable[[], object]]:
    def handler(name: str) -> Callable[[], object]:
        def read() -> object:
            return fabric.snapshot()[name]

        return read

    return {f"/v8/recovery/{name}": handler(name) for name in PROJECTIONS}


def register_routes(
    app: Any, fabric: HyperRecoveryFabric | None = None
) -> HyperRecoveryFabric:
    selected = fabric or HyperRecoveryFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path,
                handler,
                methods=["GET"],
                tags=["V8 Hyper Recovery"],
            )
        else:
            app.get(path, tags=["V8 Hyper Recovery"])(handler)
    if hasattr(app, "state"):
        app.state.v8_hyper_recovery = selected
    return selected


def create_router(fabric: HyperRecoveryFabric | None = None) -> Any:
    from fastapi import APIRouter

    router = APIRouter()
    selected = fabric or HyperRecoveryFabric()
    for path, handler in route_handlers(selected).items():
        router.get(path, tags=["v8-recovery"])(handler)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V8 Hyper Recovery", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Read-only advisory recovery projection"}
                    },
                }
            }
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "PROJECTIONS",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
