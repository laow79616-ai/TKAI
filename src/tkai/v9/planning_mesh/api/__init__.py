"""GET-only API for the V9 Adaptive Planning Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.planning_mesh.contracts import PlanningLifecycle
from tkai.v9.planning_mesh.fabric import AdaptivePlanningMesh

RESOURCES = (
    "profiles",
    "federation",
    "objectives",
    "constraints",
    "assumptions",
    "plans",
    "scenarios",
    "simulations",
    "dependencies",
    "resources",
    "schedules",
    "evaluations",
    "recommendations",
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
GET_ROUTES = tuple(f"/v9/planning/{resource}" for resource in RESOURCES)


def route_handlers(mesh: AdaptivePlanningMesh) -> dict[str, Callable[[], object]]:
    def item(resource: str) -> dict[str, object]:
        return {"items": mesh.snapshot()[resource], "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(name: str = resource) -> object:
            return item(name)

        handlers[f"/v9/planning/{resource}"] = handler
    handlers.update(
        {
            "/v9/planning/governance": mesh.governance,
            "/v9/planning/compatibility": mesh.compatibility,
            "/v9/planning/history": mesh.history,
            "/v9/planning/analytics": mesh.analytics,
            "/v9/planning/diagnostics": lambda: {"items": mesh.diagnostics()},
            "/v9/planning/health": mesh.health,
            "/v9/planning/metrics": mesh.metrics,
            "/v9/planning/audit": lambda: {"items": mesh.snapshot()["audit"]},
            "/v9/planning/lifecycle": lambda: {
                "states": tuple(item.value for item in PlanningLifecycle),
                "authorizes_execution": False,
            },
        }
    )
    return handlers


def register_routes(
    app: Any, mesh: AdaptivePlanningMesh | None = None
) -> AdaptivePlanningMesh:
    selected = mesh or AdaptivePlanningMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V9 Adaptive Planning Mesh"]
        )
    return selected


def create_router(mesh: AdaptivePlanningMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Planning Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {"200": {"description": "Advisory planning metadata"}},
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
