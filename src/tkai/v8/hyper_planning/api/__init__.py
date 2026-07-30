"""GET-only transport adapter for the V8 Hyper Planning Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_planning.fabric import HyperPlanningFabric

GET_ROUTES = tuple(
    f"/v8/planning/{name}"
    for name in (
        "profiles",
        "objectives",
        "constraints",
        "scenarios",
        "simulations",
        "resources",
        "schedules",
        "recommendations",
        "compatibility",
        "health",
        "metrics",
    )
)


def route_handlers(fabric: HyperPlanningFabric) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    def handler_for(name: str) -> Callable[[], object]:
        return lambda: items(name)

    handlers: dict[str, Callable[[], object]] = {
        f"/v8/planning/{name}": handler_for(name)
        for name in (
            "profiles",
            "objectives",
            "constraints",
            "scenarios",
            "simulations",
            "resources",
            "schedules",
            "recommendations",
            "compatibility",
        )
    }
    handlers["/v8/planning/health"] = fabric.health
    handlers["/v8/planning/metrics"] = fabric.metrics
    return handlers


def register_routes(
    app: Any, fabric: HyperPlanningFabric | None = None
) -> HyperPlanningFabric:
    selected = fabric or HyperPlanningFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Planning"]
            )
        else:
            app.get(path, tags=["V8 Hyper Planning"])(handler)
    return selected


def create_router(fabric: HyperPlanningFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Planning", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Advisory planning metadata projection"}
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
