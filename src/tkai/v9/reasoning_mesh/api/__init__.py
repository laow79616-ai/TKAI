"""GET-only transport adapter for the V9 Adaptive Reasoning Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.reasoning_mesh.contracts import ReasoningLifecycle
from tkai.v9.reasoning_mesh.fabric import AdaptiveReasoningMesh

RESOURCES = (
    "profiles",
    "federation",
    "contexts",
    "sources",
    "knowledge",
    "evidence",
    "signals",
    "observations",
    "hypotheses",
    "assumptions",
    "constraints",
    "reasoning",
    "alternatives",
    "comparisons",
    "evaluations",
    "confidence",
    "recommendations",
    "explanations",
    "reviews",
    "governance",
    "policies",
    "versions",
    "compatibility",
    "history",
    "analytics",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = tuple(f"/v9/reasoning/{resource}" for resource in RESOURCES)


def route_handlers(mesh: AdaptiveReasoningMesh) -> dict[str, Callable[[], object]]:
    def item(resource: str) -> dict[str, object]:
        return {"items": mesh.snapshot()[resource], "mode": mesh.MODE}

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(name: str = resource) -> object:
            return item(name)

        handlers[f"/v9/reasoning/{resource}"] = handler
    handlers.update(
        {
            "/v9/reasoning/federation": lambda: item("federation"),
            "/v9/reasoning/governance": mesh.governance,
            "/v9/reasoning/policies": mesh.policies,
            "/v9/reasoning/compatibility": mesh.compatibility,
            "/v9/reasoning/history": mesh.history,
            "/v9/reasoning/analytics": mesh.analytics,
            "/v9/reasoning/diagnostics": lambda: {"items": mesh.diagnostics()},
            "/v9/reasoning/health": mesh.health,
            "/v9/reasoning/metrics": mesh.metrics,
            "/v9/reasoning/audit": lambda: {"items": mesh.snapshot()["audit"]},
            "/v9/reasoning/lifecycle": lambda: {
                "states": tuple(item.value for item in ReasoningLifecycle),
                "approved_reference_authorizes_execution": False,
            },
        }
    )
    return handlers


def register_routes(
    app: Any, mesh: AdaptiveReasoningMesh | None = None
) -> AdaptiveReasoningMesh:
    selected = mesh or AdaptiveReasoningMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V9 Adaptive Reasoning Mesh"]
            )
        else:
            app.get(path, tags=["V9 Adaptive Reasoning Mesh"])(handler)
    return selected


def create_router(mesh: AdaptiveReasoningMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Reasoning Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Safe advisory reasoning metadata"}
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
