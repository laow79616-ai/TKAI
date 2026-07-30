"""GET-only API adapter for the Sovereign Governance Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.governance_mesh import SovereignGovernanceMesh

RESOURCES = (
    "profiles",
    "policies",
    "constraints",
    "reviews",
    "approvals",
    "risks",
    "compliance",
    "validation",
    "health",
    "metrics",
)
GET_ROUTES = tuple(f"/v10/governance/{resource}" for resource in RESOURCES)


def route_handlers(
    mesh: SovereignGovernanceMesh,
) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "automatic_approval": False,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/governance/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignGovernanceMesh | None = None
) -> SovereignGovernanceMesh:
    selected = mesh or SovereignGovernanceMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Governance Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Governance Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Governance Mesh"]}}
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "RESOURCES",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
