"""GET-only transport adapter for the V8 Hyper Decision Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_decision.fabric import HyperDecisionFabric

GET_ROUTES = (
    "/v8/decision/profiles",
    "/v8/decision/alternatives",
    "/v8/decision/comparisons",
    "/v8/decision/recommendations",
    "/v8/decision/reviews",
    "/v8/decision/approvals",
    "/v8/decision/compatibility",
    "/v8/decision/health",
    "/v8/decision/metrics",
)


def route_handlers(fabric: HyperDecisionFabric) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    return {
        "/v8/decision/profiles": lambda: items("profiles"),
        "/v8/decision/alternatives": lambda: items("alternatives"),
        "/v8/decision/comparisons": lambda: items("comparisons"),
        "/v8/decision/recommendations": lambda: items("recommendations"),
        "/v8/decision/reviews": lambda: items("reviews"),
        "/v8/decision/approvals": lambda: items("approvals"),
        "/v8/decision/compatibility": lambda: items("compatibility"),
        "/v8/decision/health": fabric.health,
        "/v8/decision/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: HyperDecisionFabric | None = None
) -> HyperDecisionFabric:
    selected = fabric or HyperDecisionFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Decision"]
            )
        else:
            app.get(path, tags=["V8 Hyper Decision"])(handler)
    return selected


def create_router(fabric: HyperDecisionFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Decision", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Advisory decision metadata projection"}
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
