"""Authenticated management API for TKAI Business Platform V2.0."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from server.api.auth.dependencies import AuthenticationDependency
from server.api.auth.service import ReferenceAuthenticationService

from .models import BusinessScope
from .service import MODULES, BusinessPlatform

BASE = "/business/v1"
STATIC_ROUTES = ("dashboard", "modules", "health", "audit", "settings", "exports")
GET_ROUTES = tuple(f"{BASE}/{name}" for name in STATIC_ROUTES) + tuple(
    f"{BASE}/{item.id}" for item in MODULES
)
V2_BASE = "/business/v2"
V2_ROUTES = (
    f"{V2_BASE}/records",
    f"{V2_BASE}/records/{{record_id}}",
    f"{V2_BASE}/audit",
    f"{V2_BASE}/dashboard",
    f"{V2_BASE}/reports/export",
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
    app: Any,
    platform: BusinessPlatform | None = None,
    authentication: ReferenceAuthenticationService | None = None,
    *,
    fastapi_module: Any | None = None,
) -> BusinessPlatform:
    selected = platform or BusinessPlatform()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(path, handler, methods=["GET"], tags=["business-platform-v1"])
    if authentication is not None:
        _register_v2(app, selected, authentication, fastapi_module)
    app.state.business_platform = selected
    return selected


def _register_v2(
    app: Any,
    platform: BusinessPlatform,
    authentication: ReferenceAuthenticationService,
    fastapi_module: Any | None,
) -> None:
    auth = AuthenticationDependency(authentication)
    header = (
        fastapi_module.Header
        if fastapi_module is not None
        else lambda default=None, **_: default
    )

    def scope(authorization: str | None, tenant: str, workspace: str) -> BusinessScope:
        user = auth(authorization)
        return BusinessScope(tenant, workspace, user.username)

    def records(
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
        module: str = "",
        kind: str = "",
        status: str = "",
        query: str = "",
    ) -> dict[str, Any]:
        return platform.inventory(
            scope(authorization, tenant, workspace),
            module=module,
            kind=kind,
            status=status,
            query=query,
        )

    def create(
        payload: dict[str, Any],
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.create(scope(authorization, tenant, workspace), payload)

    def detail(
        record_id: str,
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.get(scope(authorization, tenant, workspace), record_id)

    def update(
        record_id: str,
        payload: dict[str, Any],
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.update(
            scope(authorization, tenant, workspace), record_id, payload
        )

    def archive(
        record_id: str,
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.archive(scope(authorization, tenant, workspace), record_id)

    def audit_log(
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.audit(scope(authorization, tenant, workspace))

    def dashboard(
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
    ) -> dict[str, Any]:
        return platform.dashboard(scope(authorization, tenant, workspace))

    def export(
        authorization: str | None = header(default=None),
        tenant: str = header(default="default", alias="X-Tenant-ID"),
        workspace: str = header(default="default", alias="X-Workspace-ID"),
        module: str = "",
    ) -> dict[str, Any]:
        scoped = scope(authorization, tenant, workspace)
        result = platform.inventory(scoped, module=module)
        return {
            "format": "json",
            "redacted": True,
            "data": platform.redact(result["data"]),
            "total": result["total"],
        }

    routes = (
        (f"{V2_BASE}/records", records, ["GET"], "listBusinessRecordsV2"),
        (f"{V2_BASE}/records", create, ["POST"], "createBusinessRecordV2"),
        (f"{V2_BASE}/records/{{record_id}}", detail, ["GET"], "getBusinessRecordV2"),
        (
            f"{V2_BASE}/records/{{record_id}}",
            update,
            ["PATCH"],
            "updateBusinessRecordV2",
        ),
        (
            f"{V2_BASE}/records/{{record_id}}",
            archive,
            ["DELETE"],
            "archiveBusinessRecordV2",
        ),
        (f"{V2_BASE}/audit", audit_log, ["GET"], "listBusinessAuditV2"),
        (f"{V2_BASE}/dashboard", dashboard, ["GET"], "getBusinessDashboardV2"),
        (f"{V2_BASE}/reports/export", export, ["GET"], "exportBusinessReportV2"),
    )
    for path, endpoint, methods, operation_id in routes:
        app.add_api_route(
            path,
            endpoint,
            methods=methods,
            tags=["business-platform-v2"],
            operation_id=operation_id,
        )


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
