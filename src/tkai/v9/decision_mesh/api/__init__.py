"""GET-only API for the V9 Adaptive Decision Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.decision_mesh.contracts import DecisionLifecycle
from tkai.v9.decision_mesh.fabric import AdaptiveDecisionMesh

RESOURCES = (
    "profiles", "federation", "contexts", "decisions", "alternatives",
    "comparisons", "evaluations", "recommendations", "confidence", "governance",
    "reviews", "approvals", "compatibility", "history", "analytics", "diagnostics",
    "health", "metrics", "audit", "lifecycle",
)
GET_ROUTES = tuple(f"/v9/decision/{resource}" for resource in RESOURCES)


def route_handlers(mesh: AdaptiveDecisionMesh) -> dict[str, Callable[[], object]]:
    def item(resource: str) -> dict[str, object]:
        return {"items": mesh.snapshot()[resource], "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:
        def handler(name: str = resource) -> object:
            return item(name)

        handlers[f"/v9/decision/{resource}"] = handler
    handlers.update(
        {
            "/v9/decision/governance": mesh.governance,
            "/v9/decision/compatibility": mesh.compatibility,
            "/v9/decision/history": mesh.history,
            "/v9/decision/analytics": mesh.analytics,
            "/v9/decision/diagnostics": lambda: {"items": mesh.diagnostics()},
            "/v9/decision/health": mesh.health,
            "/v9/decision/metrics": mesh.metrics,
            "/v9/decision/audit": lambda: {"items": mesh.snapshot()["audit"]},
            "/v9/decision/lifecycle": lambda: {
                "states": tuple(item.value for item in DecisionLifecycle),
                "authorizes_execution": False,
            },
        }
    )
    return handlers


def register_routes(
    app: Any, mesh: AdaptiveDecisionMesh | None = None
) -> AdaptiveDecisionMesh:
    selected = mesh or AdaptiveDecisionMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V9 Adaptive Decision Mesh"]
        )
    return selected


def create_router(mesh: AdaptiveDecisionMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Decision Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {"200": {"description": "Advisory decision metadata"}},
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
