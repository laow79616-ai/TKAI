"""Framework-neutral HTTP API for the TikTok Proxy Center."""

from __future__ import annotations

from typing import Any

from ..models import (
    BindingTarget,
    GroupType,
    Proxy,
    ProxyBinding,
    ProxyGroup,
    ProxyProtocol,
    ProxyScope,
    ProxyStatus,
    ProxyType,
)
from ..service import TikTokProxyCenter

BASE = "/tiktok/proxy-center"
ROUTES = (
    f"{BASE}/proxies",
    f"{BASE}/groups",
    f"{BASE}/health",
    f"{BASE}/rotation",
    f"{BASE}/bindings",
    f"{BASE}/pool",
    f"{BASE}/statistics",
)


def register_proxy_center_routes(app: Any, center: TikTokProxyCenter) -> None:
    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "tiktok:proxy:read",
    ) -> ProxyScope:
        return ProxyScope(tenant, workspace, actor, frozenset(permissions.split(",")))

    def proxies(tenant: str, workspace: str) -> dict[str, Any]:
        values = center.list(scope(tenant, workspace))
        return {"data": [item.to_dict() for item in values], "total": len(values)}

    def create_proxy(payload: dict[str, Any]) -> dict[str, Any]:
        item_scope = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "tiktok:proxy:write")),
        )
        item = Proxy(
            str(payload["id"]),
            str(payload["name"]),
            item_scope.tenant,
            item_scope.workspace,
            ProxyType(str(payload.get("type", "ipv4"))),
            ProxyProtocol(str(payload.get("protocol", "http"))),
            str(payload["host"]),
            int(payload["port"]),
            str(payload.get("credential_reference", "")),
            str(payload.get("provider", "")),
            str(payload.get("region", "")),
            str(payload.get("country", "")),
            str(payload.get("isp", "")),
            ProxyStatus(str(payload.get("status", "draft"))),
            dict(payload.get("metadata", {})),
        )
        return center.create(item, item_scope).to_dict()

    def groups(tenant: str, workspace: str) -> dict[str, Any]:
        item_scope = scope(tenant, workspace)
        values = [
            item
            for item in center.groups.values()
            if item.tenant == tenant and item.workspace == workspace
        ]
        center._require(item_scope, "read")
        return {
            "data": [
                {"id": item.id, "name": item.name, "type": item.type.value}
                for item in values
            ],
            "total": len(values),
        }

    def create_group(payload: dict[str, Any]) -> dict[str, Any]:
        item_scope = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            permissions=str(payload.get("permissions", "tiktok:proxy:write")),
        )
        item = ProxyGroup(
            str(payload["id"]),
            str(payload["name"]),
            item_scope.tenant,
            item_scope.workspace,
            GroupType(str(payload["type"])),
            set(map(str, payload.get("proxy_ids", []))),
            dict(payload.get("dynamic_filter", {})),
        )
        center.create_group(item, item_scope)
        return {"id": item.id}

    def create_binding(payload: dict[str, Any]) -> dict[str, Any]:
        item_scope = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            permissions=str(payload.get("permissions", "tiktok:proxy:bind")),
        )
        item = ProxyBinding(
            str(payload["id"]),
            item_scope.tenant,
            item_scope.workspace,
            BindingTarget(str(payload["target_type"])),
            str(payload["target_reference"]),
            str(payload.get("proxy_reference", "")),
            str(payload.get("group_reference", "")),
            int(payload.get("priority", 0)),
            str(payload.get("affinity", "")),
            str(payload.get("sticky_session_reference", "")),
        )
        center.create_binding(item, item_scope)
        return {"id": item.id}

    def dashboard(tenant: str, workspace: str) -> dict[str, Any]:
        return center.dashboard(scope(tenant, workspace))

    app.add_api_route(ROUTES[0], proxies, methods=["GET"], tags=["tiktok"])
    app.add_api_route(ROUTES[0], create_proxy, methods=["POST"], tags=["tiktok"])
    app.add_api_route(ROUTES[1], groups, methods=["GET"], tags=["tiktok"])
    app.add_api_route(ROUTES[1], create_group, methods=["POST"], tags=["tiktok"])
    app.add_api_route(ROUTES[4], create_binding, methods=["POST"], tags=["tiktok"])
    for path in (ROUTES[2], ROUTES[3], ROUTES[4], ROUTES[5], ROUTES[6]):
        app.add_api_route(path, dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route(f"{BASE}/dashboard", dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route(
        f"{BASE}/metrics",
        center.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok"],
    )
