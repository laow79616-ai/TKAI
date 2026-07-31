"""GET-only API adapter for the Sovereign Recovery Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.recovery_mesh import SovereignRecoveryMesh

RESOURCES = (
    "profiles",
    "contexts",
    "strategies",
    "plans",
    "readiness",
    "validation",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = tuple(f"/v10/recovery/{resource}" for resource in RESOURCES)


def route_handlers(mesh: SovereignRecoveryMesh) -> dict[str, Callable[[], object]]:
    def projection(resource: str) -> object:
        if resource == "health":
            return mesh.health()
        if resource == "metrics":
            return mesh.metrics()
        if resource == "audit":
            return {"items": mesh.audit(), "read_only": True, "advisory": True}
        if resource == "lifecycle":
            return mesh.lifecycle()
        return {
            "items": mesh.serialize(mesh.discover(resource)),
            "read_only": True,
            "advisory": True,
        }

    handlers: dict[str, Callable[[], object]] = {}
    for resource in RESOURCES:

        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/recovery/{resource}"] = handler
    return handlers


def register_routes(
    app: Any, mesh: SovereignRecoveryMesh | None = None
) -> SovereignRecoveryMesh:
    selected = mesh or SovereignRecoveryMesh()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V10 Sovereign Recovery Mesh"]
        )
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Recovery Mesh"]}}
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
