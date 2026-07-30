"""GET-only API projections for V8 operations metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_operations.fabric import HyperOperationsFabric

PROJECTIONS = (
    "profiles",
    "readiness",
    "runtime",
    "resources",
    "dependencies",
    "recovery",
    "compatibility",
    "health",
    "metrics",
)
GET_ROUTES = tuple(f"/v8/operations/{name}" for name in PROJECTIONS)


def route_handlers(fabric: HyperOperationsFabric) -> dict[str, Callable[[], object]]:
    def handler(name: str) -> Callable[[], object]:
        def get_projection() -> object:
            value = fabric.snapshot()[name]
            if isinstance(value, (list, tuple)):
                return {
                    "items": value,
                    "advisory": True,
                    "read_only": True,
                    "execution_authorized": False,
                }
            return value

        return get_projection

    return {f"/v8/operations/{name}": handler(name) for name in PROJECTIONS}


def register_routes(
    app: Any, fabric: HyperOperationsFabric | None = None
) -> HyperOperationsFabric:
    selected = fabric or HyperOperationsFabric()
    for path, route in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, route, methods=["GET"], tags=["V8 Hyper Operations"]
            )
        else:
            app.get(path, tags=["V8 Hyper Operations"])(route)
    return selected


def create_router(fabric: HyperOperationsFabric | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the router") from error
    router = APIRouter()
    register_routes(router, fabric)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V8 Hyper Operations", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {
                            "description": "Read-only advisory operations projection"
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
