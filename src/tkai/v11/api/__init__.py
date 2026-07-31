"""GET-only API adapter for the V11 Autonomous Intelligence Core."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v11.autonomous_core import AutonomousIntelligenceCore

RESOURCES = (
    "core",
    "profile",
    "contexts",
    "knowledge",
    "reasoning",
    "decision",
    "planning",
    "operations",
    "recovery",
    "governance",
    "trust",
    "integrity",
    "compatibility",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
)
GET_ROUTES = (
    "/v11/intelligence",
    *(f"/v11/intelligence/{resource}" for resource in RESOURCES),
)
FORBIDDEN_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def route_handlers(
    core: AutonomousIntelligenceCore,
) -> dict[str, Callable[[], object]]:
    handlers: dict[str, Callable[[], object]] = {
        "/v11/intelligence": core.overview,
        "/v11/intelligence/core": core.core,
        "/v11/intelligence/profile": core.profile,
        "/v11/intelligence/contexts": core.contexts,
        "/v11/intelligence/compatibility": core.compatibility,
        "/v11/intelligence/validation": core.validation,
        "/v11/intelligence/diagnostics": core.diagnostics,
        "/v11/intelligence/health": core.health,
        "/v11/intelligence/metrics": core.metrics,
        "/v11/intelligence/audit": core.audit,
    }
    for resource in (
        "knowledge",
        "reasoning",
        "decision",
        "planning",
        "operations",
        "recovery",
        "governance",
        "trust",
        "integrity",
    ):

        def handler(resource: str = resource) -> object:
            return core.references(resource)

        handlers[f"/v11/intelligence/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, core: AutonomousIntelligenceCore | None = None
) -> AutonomousIntelligenceCore:
    selected = core or AutonomousIntelligenceCore()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path,
                handler,
                methods=["GET"],
                tags=["V11 Autonomous Intelligence"],
            )
        else:
            app.get(path, tags=["V11 Autonomous Intelligence"])(handler)
    return selected


def create_router(core: AutonomousIntelligenceCore | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the V11 router.") from error
    router = APIRouter()
    register_routes(router, core)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V11 Autonomous Intelligence"]}}
            for path in GET_ROUTES
        },
    }


__all__ = (
    "FORBIDDEN_METHODS",
    "GET_ROUTES",
    "RESOURCES",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
