"""GET-only transport adapter for the TKAI V10 Sovereign Core."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v10.sovereign_core import SovereignCore

RESOURCES = (
    "trust",
    "identities",
    "principals",
    "integrity",
    "attestations",
    "boundaries",
    "control-plane",
    "frameworks",
    "capabilities",
    "services",
    "modules",
    "extensions",
    "runtime",
    "registries",
    "discovery",
    "topology",
    "dependencies",
    "relationships",
    "contexts",
    "policies",
    "constraints",
    "compatibility",
    "negotiation",
    "change-plans",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = ("/v10/core", *(f"/v10/core/{resource}" for resource in RESOURCES))


def route_handlers(core: SovereignCore) -> dict[str, Callable[[], object]]:
    registry_aliases = {"trust": "trust_domains", "control-plane": "diagnostics"}

    def projection(resource: str) -> object:
        if resource == "topology":
            return {
                "nodes": core.serialize(core.topology.nodes()),
                "edges": core.serialize(core.topology.edges()),
                "executable": False,
            }
        if resource == "dependencies":
            return {"issues": core.topology.issues()}
        if resource in {"compatibility", "negotiation"}:
            return core.negotiate("v9")
        if resource == "validation":
            return core.validation()
        if resource == "diagnostics":
            return {"items": core.diagnostics()}
        if resource == "health":
            return core.health()
        if resource == "metrics":
            return core.metrics()
        if resource == "audit":
            return {"items": core.audit()}
        if resource == "lifecycle":
            return core.lifecycle()
        if resource == "registries":
            return {"registries": core.overview()["registries"]}
        if resource == "contexts":
            return {"items": core.serialize(core._contexts)}
        name = registry_aliases.get(resource, resource.replace("-", "_"))
        if name in core.registries.NAMES:
            return {"items": core.serialize(core.discover(name))}
        return {"items": (), "read_only": True}

    handlers: dict[str, Callable[[], object]] = {"/v10/core": core.overview}
    for resource in RESOURCES:
        def handler(resource: str = resource) -> object:
            return projection(resource)

        handlers[f"/v10/core/{resource}"] = handler
    return handlers


def register_routes(app: Any, core: SovereignCore | None = None) -> SovereignCore:
    selected = core or SovereignCore()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V10 Sovereign Core"]
            )
        else:
            app.get(path, tags=["V10 Sovereign Core"])(handler)
    return selected


def create_router(core: SovereignCore | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the V10 router.") from error
    router = APIRouter()
    register_routes(router, core)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V10 Sovereign Core"]}} for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "RESOURCES",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
