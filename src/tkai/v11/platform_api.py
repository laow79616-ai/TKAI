"""GET-only HTTP adapter for the complete TKAI V11 platform."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from tkai.v11.platform import COMPONENTS, V11Platform

PROJECTIONS = ("overview", "health", "diagnostics", "metrics", "audit")
GET_ROUTES = (
    "/v11",
    *(
        path
        for component in COMPONENTS
        for path in (
            f"/v11/{component.slug}",
            *(f"/v11/{component.slug}/{name}" for name in PROJECTIONS),
        )
    ),
)


def route_handlers(platform: V11Platform) -> dict[str, Callable[[], object]]:
    handlers: dict[str, Callable[[], object]] = {"/v11": platform.overview}
    for component in COMPONENTS:
        slug = component.slug
        handlers[f"/v11/{slug}"] = partial(platform.component, slug)
        handlers[f"/v11/{slug}/overview"] = partial(platform.component, slug)
        handlers[f"/v11/{slug}/health"] = partial(platform.health, slug)
        handlers[f"/v11/{slug}/diagnostics"] = partial(platform.diagnostics, slug)
        handlers[f"/v11/{slug}/metrics"] = partial(platform.metrics, slug)
        handlers[f"/v11/{slug}/audit"] = partial(platform.audit, slug)
    return handlers


def register_routes(app: Any, platform: V11Platform | None = None) -> V11Platform:
    selected = platform or V11Platform()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(path, handler, methods=["GET"], tags=["TKAI V11"])
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V11", "version": "11.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "v11_"
                    + path.strip("/").replace("/", "_").replace("-", "_")
                }
            }
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "PROJECTIONS",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
