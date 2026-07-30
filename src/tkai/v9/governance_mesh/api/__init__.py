"""GET-only transport adapter for the V9 Adaptive Governance Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.governance_mesh.fabric import AdaptiveGovernanceMesh

GET_ROUTES = (
    "/v9/governance/profiles",
    "/v9/governance/federation",
    "/v9/governance/policies",
    "/v9/governance/constraints",
    "/v9/governance/compliance",
    "/v9/governance/reviews",
    "/v9/governance/approvals",
    "/v9/governance/compatibility",
    "/v9/governance/health",
    "/v9/governance/metrics",
)


def route_handlers(
    fabric: AdaptiveGovernanceMesh,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {
            "items": fabric.snapshot()[name],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        }

    return {
        "/v9/governance/profiles": lambda: items("profiles"),
        "/v9/governance/federation": lambda: {
            "sources": fabric.snapshot()["sources"],
            "relationships": fabric.snapshot()["relationships"],
            "mode": "reference-only",
            "advisory": True,
            "execution_authorized": False,
        },
        "/v9/governance/policies": lambda: items("policies"),
        "/v9/governance/constraints": lambda: items("constraints"),
        "/v9/governance/compliance": lambda: items("compliance"),
        "/v9/governance/reviews": lambda: items("reviews"),
        "/v9/governance/approvals": lambda: items("approvals"),
        "/v9/governance/compatibility": lambda: items("compatibility"),
        "/v9/governance/health": fabric.health,
        "/v9/governance/metrics": fabric.metrics,
    }


def register_routes(
    app: Any, fabric: AdaptiveGovernanceMesh | None = None
) -> AdaptiveGovernanceMesh:
    selected = fabric or AdaptiveGovernanceMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V9 Adaptive Governance Mesh"]
            )
        else:
            app.get(path, tags=["V9 Adaptive Governance Mesh"])(handler)
    return selected


def create_router(fabric: AdaptiveGovernanceMesh | None = None) -> Any:
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
        "info": {"title": "TKAI V9 Adaptive Governance Mesh", "version": "9.0.0"},
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

