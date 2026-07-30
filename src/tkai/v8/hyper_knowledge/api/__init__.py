"""GET-only transport adapter for the V8 Hyper Knowledge Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric

GET_ROUTES = (
    "/v8/knowledge/profiles",
    "/v8/knowledge/ontology",
    "/v8/knowledge/entities",
    "/v8/knowledge/relationships",
    "/v8/knowledge/evidence",
    "/v8/knowledge/lineage",
    "/v8/knowledge/compatibility",
    "/v8/knowledge/health",
    "/v8/knowledge/metrics",
)


def route_handlers(
    fabric: HyperKnowledgeFabric,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    return {
        "/v8/knowledge/profiles": lambda: items("profiles"),
        "/v8/knowledge/ontology": lambda: items("ontology"),
        "/v8/knowledge/entities": lambda: items("entities"),
        "/v8/knowledge/relationships": lambda: items("relationships"),
        "/v8/knowledge/evidence": lambda: items("evidence"),
        "/v8/knowledge/lineage": lambda: items("lineage"),
        "/v8/knowledge/compatibility": lambda: items("compatibility"),
        "/v8/knowledge/health": fabric.health,
        "/v8/knowledge/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: HyperKnowledgeFabric | None = None
) -> HyperKnowledgeFabric:
    selected = fabric or HyperKnowledgeFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Knowledge"]
            )
        else:
            app.get(path, tags=["V8 Hyper Knowledge"])(handler)
    return selected


def create_router(fabric: HyperKnowledgeFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Knowledge", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {
                            "description": "Advisory knowledge metadata projection"
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
