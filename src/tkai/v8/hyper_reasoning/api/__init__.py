"""GET-only transport adapter for the V8 Hyper Reasoning Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric

GET_ROUTES = (
    "/v8/reasoning/profiles",
    "/v8/reasoning/evidence",
    "/v8/reasoning/knowledge",
    "/v8/reasoning/confidence",
    "/v8/reasoning/recommendations",
    "/v8/reasoning/explanations",
    "/v8/reasoning/compatibility",
    "/v8/reasoning/health",
    "/v8/reasoning/metrics",
)


def route_handlers(
    fabric: HyperReasoningFabric,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    return {
        "/v8/reasoning/profiles": lambda: items("profiles"),
        "/v8/reasoning/evidence": lambda: items("evidence"),
        "/v8/reasoning/knowledge": lambda: items("knowledge"),
        "/v8/reasoning/confidence": lambda: items("confidence"),
        "/v8/reasoning/recommendations": lambda: items("recommendations"),
        "/v8/reasoning/explanations": lambda: items("explanations"),
        "/v8/reasoning/compatibility": lambda: items("compatibility"),
        "/v8/reasoning/health": fabric.health,
        "/v8/reasoning/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: HyperReasoningFabric | None = None
) -> HyperReasoningFabric:
    selected = fabric or HyperReasoningFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Reasoning"]
            )
        else:
            app.get(path, tags=["V8 Hyper Reasoning"])(handler)
    return selected


def create_router(fabric: HyperReasoningFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Reasoning", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {
                            "description": "Advisory reasoning metadata projection"
                        }
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
