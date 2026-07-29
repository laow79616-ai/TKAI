"""GET-only transport adapter for V8 Hyper Coordination."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_coordination.coordination import HyperCoordinationFramework

GET_ROUTES = (
    "/v8/coordination/profiles",
    "/v8/coordination/frameworks",
    "/v8/coordination/dependencies",
    "/v8/coordination/relationships",
    "/v8/coordination/synchronization",
    "/v8/coordination/compatibility",
    "/v8/coordination/governance",
    "/v8/coordination/health",
    "/v8/coordination/metrics",
)


def route_handlers(
    framework: HyperCoordinationFramework,
) -> dict[str, Callable[[], object]]:
    """Build transport-neutral read handlers."""

    return {
        "/v8/coordination/profiles": lambda: {
            "items": framework.snapshot()["profiles"]
        },
        "/v8/coordination/frameworks": lambda: {
            "items": framework.snapshot()["frameworks"]
        },
        "/v8/coordination/dependencies": lambda: framework.snapshot()[
            "dependencies"
        ],
        "/v8/coordination/relationships": lambda: {
            "items": framework.snapshot()["relationships"]
        },
        "/v8/coordination/synchronization": lambda: {
            "items": framework.snapshot()["synchronization"],
            "runtime_synchronization": "disabled",
        },
        "/v8/coordination/compatibility": lambda: framework.snapshot()[
            "compatibility"
        ],
        "/v8/coordination/governance": lambda: framework.snapshot()["governance"],
        "/v8/coordination/health": framework.health,
        "/v8/coordination/metrics": framework.metrics,
    }


def register_routes(
    app: Any, framework: HyperCoordinationFramework | None = None
) -> HyperCoordinationFramework:
    """Register only GET endpoints on a compatible web host."""

    selected = framework or HyperCoordinationFramework()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path,
                handler,
                methods=["GET"],
                tags=["V8 Hyper Coordination"],
            )
        else:
            app.get(path, tags=["V8 Hyper Coordination"])(handler)
    return selected


def create_router(
    framework: HyperCoordinationFramework | None = None,
) -> Any:
    """Create an optional FastAPI router."""

    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the router.") from error
    router = APIRouter()
    register_routes(router, framework)
    return router


def openapi_contract() -> dict[str, object]:
    """Return the static GET-only OpenAPI path fragment."""

    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V8 Hyper Coordination", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {"200": {"description": "Coordination metadata"}},
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
