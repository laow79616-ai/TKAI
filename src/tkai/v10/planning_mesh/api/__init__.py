"""GET-only API adapter for the Sovereign Planning Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.planning_mesh import SovereignPlanningMesh

RESOURCES = (
    "profiles",
    "contexts",
    "objectives",
    "milestones",
    "dependencies",
    "timelines",
    "readiness",
    "validation",
    "health",
    "metrics",
)
GET_ROUTES = tuple(f"/v10/planning/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignPlanningMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "advisory": True,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/planning/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignPlanningMesh | None = None
) -> SovereignPlanningMesh:
    selected = mesh or SovereignPlanningMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Planning Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Planning Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Planning Mesh"]}}
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
