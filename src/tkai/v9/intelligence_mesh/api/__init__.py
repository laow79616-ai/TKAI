"""GET-only transport adapter for the V8 Adaptive Intelligence Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh

GET_ROUTES = (
    "/v9/intelligence/profiles",
    "/v9/intelligence/federation",
    "/v9/intelligence/knowledge",
    "/v9/intelligence/evidence",
    "/v9/intelligence/signals",
    "/v9/intelligence/recommendations",
    "/v9/intelligence/compatibility",
    "/v9/intelligence/health",
    "/v9/intelligence/metrics",
)


def route_handlers(
    fabric: AdaptiveIntelligenceMesh,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {"items": fabric.snapshot()[name], "mode": "reference-only"}

    return {
        "/v9/intelligence/profiles": lambda: items("profiles"),
        "/v9/intelligence/federation": lambda: {
            "sources": fabric.snapshot()["sources"],
            "relationships": fabric.snapshot()["relationships"],
            "mode": "reference-only",
        },
        "/v9/intelligence/knowledge": lambda: items("knowledge"),
        "/v9/intelligence/evidence": lambda: items("evidence"),
        "/v9/intelligence/signals": lambda: items("signals"),
        "/v9/intelligence/recommendations": lambda: items("recommendations"),
        "/v9/intelligence/compatibility": lambda: items("compatibility"),
        "/v9/intelligence/health": fabric.health,
        "/v9/intelligence/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: AdaptiveIntelligenceMesh | None = None
) -> AdaptiveIntelligenceMesh:
    selected = fabric or AdaptiveIntelligenceMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V9 Adaptive Intelligence Mesh"]
            )
        else:
            app.get(path, tags=["V9 Adaptive Intelligence Mesh"])(handler)
    return selected


def create_router(fabric: AdaptiveIntelligenceMesh | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the router.") from error
    router = APIRouter()
    register_routes(router, fabric)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V9 Adaptive Intelligence Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Reference-only intelligence metadata"}
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
