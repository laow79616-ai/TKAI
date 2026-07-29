"""GET-only FastAPI-compatible adapter for the TKAI V8 Hyper Kernel."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v8.kernel import HyperKernel

GET_ROUTES = (
    "/v8/kernel",
    "/v8/frameworks",
    "/v8/capabilities",
    "/v8/runtime",
    "/v8/health",
    "/v8/metrics",
    "/v8/diagnostics",
)


def route_handlers(kernel: HyperKernel) -> dict[str, Callable[[], object]]:
    """Create transport-neutral handlers for every public V8 endpoint."""

    return {
        "/v8/kernel": kernel.overview,
        "/v8/frameworks": lambda: {
            "items": [
                kernel.serialize_record(record)
                for record in kernel.framework_registry.discover()
            ]
        },
        "/v8/capabilities": lambda: {
            "items": [
                kernel.serialize_record(record)
                for record in kernel.capability_registry.discover()
            ]
        },
        "/v8/runtime": lambda: {
            "items": [
                kernel.serialize_record(record)
                for record in kernel.runtime_registry.discover()
            ]
        },
        "/v8/health": kernel.health,
        "/v8/metrics": kernel.metrics,
        "/v8/diagnostics": lambda: {
            "items": [
                kernel.serialize_diagnostic(item) for item in kernel.diagnostics()
            ]
        },
    }


def register_routes(app: Any, kernel: HyperKernel | None = None) -> HyperKernel:
    """Register GET-only endpoints on a FastAPI-compatible host."""

    selected = kernel or HyperKernel()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V8 Hyper Kernel"]
            )
        else:
            app.get(path, tags=["V8 Hyper Kernel"])(handler)
    return selected


def create_router(kernel: HyperKernel | None = None) -> Any:
    """Create an optional FastAPI router without a core FastAPI dependency."""

    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the V8 router.") from error
    router = APIRouter()
    register_routes(router, kernel)
    return router


__all__ = ("GET_ROUTES", "create_router", "register_routes", "route_handlers")
