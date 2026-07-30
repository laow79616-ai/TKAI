"""GET-only compatibility API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.compatibility_mesh import SovereignCompatibilityMesh

RESOURCES = tuple(
    """
    profiles versions subjects contracts interfaces schemas capabilities frameworks
    modules services extensions configuration storage runtime apis openapi dashboard
    ai-studio deployment integrity trust governance rules negotiations assessments
    gaps conflicts plans validation diagnostics health metrics audit lifecycle
    """.split()
)
GET_ROUTES = tuple(f"/v10/compatibility/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignCompatibilityMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        if resource == "diagnostics":
            return mesh.diagnostics()
        if resource == "audit":
            return mesh.serialize(mesh.audit())
        return {
            "items": mesh.serialize(mesh.discover(resource.replace("-", "_"))),
            "read_only": True,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def make_handler(selected: str) -> Callable[[], object]:
            def handler() -> object:
                return projection(selected)

            return handler

        handlers[f"/v10/compatibility/{resource}"] = make_handler(resource)
    return handlers


def register_routes(
    app: Any, mesh: SovereignCompatibilityMesh | None = None
) -> SovereignCompatibilityMesh:
    selected = mesh or SovereignCompatibilityMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path,
                handler,
                methods=["GET"],
                tags=["V10 Sovereign Compatibility Mesh"],
            )
        else:
            app.get(path, tags=["V10 Sovereign Compatibility Mesh"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {
                "get": {
                    "operationId": (
                        f"getV10Compatibility{resource.title().replace('-', '')}"
                    )
                }
            }
            for path, resource in zip(GET_ROUTES, RESOURCES, strict=True)
        },
    }
