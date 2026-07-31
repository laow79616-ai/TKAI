"""GET-only OpenAPI surface for TKAI Business Platform V1.0."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .models import BusinessScope
from .service import MODULES, BusinessPlatform

BASE = "/business/v1"
STATIC_ROUTES = ("dashboard", "modules", "health", "audit", "settings", "exports")
GET_ROUTES = tuple(f"{BASE}/{name}" for name in STATIC_ROUTES) + tuple(
    f"{BASE}/{item.id}" for item in MODULES
)


def _scope(
    tenant: str = "default", workspace: str = "default", actor: str = "api"
) -> BusinessScope:
    return BusinessScope(tenant, workspace, actor)


def route_handlers(
    platform: BusinessPlatform,
) -> dict[str, Callable[..., dict[str, Any]]]:
    handlers: dict[str, Callable[..., dict[str, Any]]] = {
        f"{BASE}/dashboard": lambda tenant="default", workspace="default": (
            platform.dashboard(_scope(tenant, workspace))
        ),
        f"{BASE}/modules": lambda: platform.modules(),
        f"{BASE}/health": lambda tenant="default", workspace="default": platform.health(
            _scope(tenant, workspace)
        ),
        f"{BASE}/audit": lambda tenant="default", workspace="default": platform.audit(
            _scope(tenant, workspace)
        ),
        f"{BASE}/settings": lambda tenant="default", workspace="default": (
            platform.settings(_scope(tenant, workspace))
        ),
        f"{BASE}/exports": lambda tenant="default", workspace="default", module="": (
            platform.export_metadata(_scope(tenant, workspace), module)
        ),
    }
    for definition in MODULES:
        handlers[f"{BASE}/{definition.id}"] = _module_handler(platform, definition.id)
    return handlers


def _module_handler(
    platform: BusinessPlatform, module_id: str
) -> Callable[..., dict[str, Any]]:
    def handler(tenant: str = "default", workspace: str = "default") -> dict[str, Any]:
        return platform.module(module_id, _scope(tenant, workspace))

    handler.__name__ = f"business_{module_id.replace('-', '_')}"
    return handler


def register_business_platform_routes(
    app: Any, platform: BusinessPlatform | None = None
) -> BusinessPlatform:
    selected = platform or BusinessPlatform()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(path, handler, methods=["GET"], tags=["business-platform"])
    app.state.business_platform = selected
    return selected


def openapi_contract() -> dict[str, Any]:
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "TKAI Business Platform API",
            "version": "1.0.0",
            "description": (
                "Tenant-scoped metadata and advisory API. No execution, publishing, "
                "browser-launch, or proxy-switching routes."
            ),
        },
        "paths": {
            path: {
                "get": {
                    "operationId": "get"
                    + path.title().replace("/", "").replace("-", ""),
                    "responses": {"200": {"description": "Business metadata response"}},
                }
            }
            for path in GET_ROUTES
        },
    }
