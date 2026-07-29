"""GET-only transport adapter for the V8 Hyper Intelligence Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_intelligence.fabric import HyperIntelligenceFabric

GET_ROUTES = (
    "/v8/intelligence/profiles",
    "/v8/intelligence/knowledge",
    "/v8/intelligence/evidence",
    "/v8/intelligence/signals",
    "/v8/intelligence/recommendations",
    "/v8/intelligence/compatibility",
    "/v8/intelligence/health",
    "/v8/intelligence/metrics",
)


def route_handlers(
    fabric: HyperIntelligenceFabric,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {"items": fabric.snapshot()[name], "mode": "reference-only"}

    return {
        "/v8/intelligence/profiles": lambda: items("profiles"),
        "/v8/intelligence/knowledge": lambda: items("knowledge"),
        "/v8/intelligence/evidence": lambda: items("evidence"),
        "/v8/intelligence/signals": lambda: items("signals"),
        "/v8/intelligence/recommendations": lambda: items("recommendations"),
        "/v8/intelligence/compatibility": lambda: items("compatibility"),
        "/v8/intelligence/health": fabric.health,
        "/v8/intelligence/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: HyperIntelligenceFabric | None = None
) -> HyperIntelligenceFabric:
    selected = fabric or HyperIntelligenceFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Intelligence"]
            )
        else:
            app.get(path, tags=["V8 Hyper Intelligence"])(handler)
    return selected


def create_router(fabric: HyperIntelligenceFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Intelligence", "version": "8.0.0"},
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
