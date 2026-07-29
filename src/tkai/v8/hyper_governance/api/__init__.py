"""GET-only transport adapter for the V8 Hyper Governance Fabric."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.hyper_governance.fabric import HyperGovernanceFabric

GET_ROUTES = (
    "/v8/governance/profiles",
    "/v8/governance/policies",
    "/v8/governance/constraints",
    "/v8/governance/compliance",
    "/v8/governance/reviews",
    "/v8/governance/approvals",
    "/v8/governance/compatibility",
    "/v8/governance/health",
    "/v8/governance/metrics",
)


def route_handlers(
    fabric: HyperGovernanceFabric,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    return {
        "/v8/governance/profiles": lambda: items("profiles"),
        "/v8/governance/policies": lambda: items("policies"),
        "/v8/governance/constraints": lambda: items("constraints"),
        "/v8/governance/compliance": lambda: items("compliance"),
        "/v8/governance/reviews": lambda: items("reviews"),
        "/v8/governance/approvals": lambda: items("approvals"),
        "/v8/governance/compatibility": lambda: items("compatibility"),
        "/v8/governance/health": fabric.health,
        "/v8/governance/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: HyperGovernanceFabric | None = None
) -> HyperGovernanceFabric:
    selected = fabric or HyperGovernanceFabric()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Governance"]
            )
        else:
            app.get(path, tags=["V8 Hyper Governance"])(handler)
    return selected


def create_router(fabric: HyperGovernanceFabric | None = None) -> Any:
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
        "info": {"title": "TKAI V8 Hyper Governance", "version": "8.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {
                            "description": "Advisory governance metadata projection"
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
