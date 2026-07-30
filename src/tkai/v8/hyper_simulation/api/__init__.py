"""GET-only API projections for V8 simulation metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_simulation.fabric import HyperSimulationFabric

PROJECTIONS = (
    "profiles",
    "inputs",
    "baselines",
    "models",
    "scenarios",
    "simulations",
    "forecasts",
    "trends",
    "capacity",
    "resources",
    "schedules",
    "dependencies",
    "risks",
    "uncertainty",
    "confidence",
    "assumptions",
    "constraints",
    "comparisons",
    "evaluations",
    "validation",
    "recommendations",
    "reviews",
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
GET_ROUTES = tuple(f"/v8/simulation/{name}" for name in PROJECTIONS)


def route_handlers(fabric: HyperSimulationFabric) -> dict[str, Callable[[], object]]:
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

    return {f"/v8/simulation/{name}": handler(name) for name in PROJECTIONS}


def register_routes(
    app: Any, fabric: HyperSimulationFabric | None = None
) -> HyperSimulationFabric:
    selected = fabric or HyperSimulationFabric()
    for path, route in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, route, methods=["GET"], tags=["V8 Hyper Simulation"]
            )
        else:
            app.get(path, tags=["V8 Hyper Simulation"])(route)
    return selected


def create_router(fabric: HyperSimulationFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Simulation", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Read-only advisory projection"}
                    },
                }
            }
            for path in GET_ROUTES
        },
    }
