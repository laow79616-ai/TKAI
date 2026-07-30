"""GET-only API adapter for the Sovereign Reasoning Mesh."""
# ruff: noqa: E501

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.reasoning_mesh import SovereignReasoningMesh

RESOURCES = tuple(
    """profiles contexts claims premises evidence inferences assumptions constraints alternatives
confidence uncertainty contradictions explanations assessments compatibility governance integrity trust
knowledge validation diagnostics health metrics audit lifecycle""".split()
)
GET_ROUTES = tuple(f"/v10/reasoning/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignReasoningMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        if resource == "diagnostics":
            return mesh.diagnostics()
        if resource == "audit":
            return mesh.audit()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "advisory": True,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/reasoning/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignReasoningMesh | None = None
) -> SovereignReasoningMesh:
    selected = mesh or SovereignReasoningMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Reasoning Mesh"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Reasoning Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Reasoning Mesh"]}}
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
