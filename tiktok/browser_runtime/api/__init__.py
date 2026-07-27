"""Framework-neutral API routes for the TikTok browser runtime."""

from __future__ import annotations

from typing import Any

from ..models import (
    BrowserEngine,
    BrowserInstance,
    BrowserProfile,
    ContextMode,
    RuntimeScope,
)
from ..service import TikTokBrowserRuntime

BASE = "/tiktok/browser-runtime"
ROUTES = (
    f"{BASE}/instances",
    f"{BASE}/profiles",
    f"{BASE}/contexts",
    f"{BASE}/pages",
    f"{BASE}/storage",
    f"{BASE}/pool",
    f"{BASE}/queue",
    f"{BASE}/health",
    f"{BASE}/recovery",
)


def register_browser_runtime_routes(app: Any, runtime: TikTokBrowserRuntime) -> None:
    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "tiktok:browser:read",
    ) -> RuntimeScope:
        return RuntimeScope(tenant, workspace, actor, frozenset(permissions.split(",")))

    def instances(tenant: str, workspace: str) -> dict[str, Any]:
        values = runtime.list_instances(scope(tenant, workspace))
        return {"data": [item.to_dict() for item in values], "total": len(values)}

    def create_instance(payload: dict[str, Any]) -> dict[str, Any]:
        item_scope = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "tiktok:browser:write")),
        )
        item = BrowserInstance(
            id=str(payload["id"]),
            name=str(payload["name"]),
            account_reference=str(payload.get("account_reference", "")),
            tenant=item_scope.tenant,
            workspace=item_scope.workspace,
            owner=str(payload.get("owner", item_scope.actor)),
            engine=BrowserEngine(str(payload.get("engine", "chromium"))),
            profile_reference=str(payload.get("profile_reference", "")),
            proxy_reference=str(payload.get("proxy_reference", "")),
            headless=bool(payload.get("headless", True)),
            context_mode=ContextMode(str(payload.get("context_mode", "ephemeral"))),
            metadata=dict(payload.get("metadata", {})),
        )
        return runtime.create_instance(item, item_scope).to_dict()

    def create_profile(payload: dict[str, Any]) -> dict[str, Any]:
        item_scope = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "tiktok:browser:write")),
        )
        profile = BrowserProfile(
            id=str(payload["id"]),
            tenant=item_scope.tenant,
            workspace=item_scope.workspace,
            account_reference=str(payload.get("account_reference", "")),
            profile_directory_reference=str(
                payload.get("profile_directory_reference", "")
            ),
            user_agent=str(payload.get("user_agent", "")),
            timezone=str(payload.get("timezone", "UTC")),
            locale=str(payload.get("locale", "en-US")),
        )
        runtime.create_profile(profile, item_scope)
        return {"id": profile.id}

    def dashboard(tenant: str, workspace: str) -> dict[str, Any]:
        return runtime.dashboard(scope(tenant, workspace))

    app.add_api_route(ROUTES[0], instances, methods=["GET"], tags=["tiktok"])
    app.add_api_route(ROUTES[0], create_instance, methods=["POST"], tags=["tiktok"])
    app.add_api_route(ROUTES[1], create_profile, methods=["POST"], tags=["tiktok"])
    for path in ROUTES[2:]:
        app.add_api_route(path, dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route(f"{BASE}/dashboard", dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route(
        f"{BASE}/metrics",
        runtime.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok"],
    )
