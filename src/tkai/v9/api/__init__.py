"""GET-only transport adapter for the V9 Adaptive Meta-Kernel."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.meta_kernel import AdaptiveMetaKernel

_RESOURCES = (
    "frameworks",
    "capabilities",
    "services",
    "modules",
    "extensions",
    "contexts",
    "adaptations",
    "policies",
    "constraints",
    "change-plans",
)
GET_ROUTES = (
    "/v9/kernel",
    *(f"/v9/kernel/{resource}" for resource in _RESOURCES),
    "/v9/kernel/topology",
    "/v9/kernel/dependencies",
    "/v9/kernel/compatibility",
    "/v9/kernel/version-negotiation",
    "/v9/kernel/validation",
    "/v9/kernel/diagnostics",
    "/v9/kernel/health",
    "/v9/kernel/metrics",
    "/v9/kernel/audit",
    "/v9/kernel/lifecycle",
)


def route_handlers(kernel: AdaptiveMetaKernel) -> dict[str, Callable[[], object]]:
    def registry(name: str) -> dict[str, object]:
        normalized = name.replace("-", "_")
        return {
            "items": [
                kernel.serialize(item)
                for item in kernel.registries.get(normalized).discover()
            ]
        }

    handlers: dict[str, Callable[[], object]] = {"/v9/kernel": kernel.overview}
    for resource in _RESOURCES:

        def handler(resource: str = resource) -> object:
            return registry(resource)

        handlers[f"/v9/kernel/{resource}"] = handler
    handlers.update(
        {
            "/v9/kernel/topology": lambda: {
                "nodes": kernel.serialize(kernel.topology.nodes()),
                "edges": kernel.serialize(kernel.topology.edges()),
                "executable": False,
            },
            "/v9/kernel/dependencies": lambda: {"issues": kernel.topology.issues()},
            "/v9/kernel/compatibility": lambda: kernel.negotiate("v8", "v9"),
            "/v9/kernel/version-negotiation": kernel.version_negotiation,
            "/v9/kernel/validation": kernel.validation,
            "/v9/kernel/diagnostics": lambda: {"items": kernel.diagnostics()},
            "/v9/kernel/health": kernel.health,
            "/v9/kernel/metrics": kernel.metrics,
            "/v9/kernel/audit": lambda: {"items": kernel.audit()},
            "/v9/kernel/lifecycle": kernel.lifecycle,
        }
    )
    return handlers


def register_routes(
    app: Any, kernel: AdaptiveMetaKernel | None = None
) -> AdaptiveMetaKernel:
    selected = kernel or AdaptiveMetaKernel()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V9 Adaptive Meta-Kernel"]
            )
        else:
            app.get(path, tags=["V9 Adaptive Meta-Kernel"])(handler)
    return selected


def create_router(kernel: AdaptiveMetaKernel | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the V9 router.") from error
    router = APIRouter()
    register_routes(router, kernel)
    return router


__all__ = ("GET_ROUTES", "create_router", "register_routes", "route_handlers")
