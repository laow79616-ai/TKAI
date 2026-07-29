"""FastAPI-compatible routes for Enterprise AI API Management."""

from dataclasses import asdict
from typing import Any

from api_management import (
    ApiManagementPlatform,
    ApiScope,
    ApiStatus,
    ApiVersion,
    Credential,
    Gateway,
    ManagedApi,
    Policy,
    Quota,
    RateLimit,
    Route,
    Subscription,
    SubscriptionStatus,
    Visibility,
)


def register_api_management_routes(app: Any, platform: ApiManagementPlatform) -> None:
    """Register the API-management control-plane resource contract."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(
            f"/api-management{path}",
            endpoint,
            methods=methods,
            tags=["api-management"],
        )

    def scope(payload: dict[str, Any] | None = None, **values: str) -> ApiScope:
        data: dict[str, Any] = payload or values
        permissions = str(data.get("permissions", "api-management:read")).split(",")
        return ApiScope(
            str(data["tenant"]),
            str(data["workspace"]),
            str(data.get("actor", "api")),
            frozenset(permissions),
            frozenset(str(data.get("scopes", "")).split(",")) - {""},
            data.get("application"),
            data.get("agent"),
        )

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    def create_api(payload: dict[str, Any]) -> dict[str, Any]:
        item = ManagedApi(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["description"]),
            str(payload["owner"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["version"]),
            str(payload["base_path"]),
            ApiStatus(str(payload.get("status", "draft"))),
            Visibility(str(payload.get("visibility", "private"))),
            dict(payload.get("metadata", {})),
        )
        return platform.create_api(item, scope(payload)).to_dict()

    def create_gateway(payload: dict[str, Any]) -> dict[str, Any]:
        item = Gateway(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("health_check", "/health")),
        )
        return platform.add_gateway(item, scope(payload)).to_dict()

    def create_route(payload: dict[str, Any]) -> dict[str, Any]:
        item = Route(
            str(payload["id"]),
            str(payload["api_id"]),
            str(payload["gateway_id"]),
            str(payload["path"]),
            tuple(payload["methods"]),
            str(payload["upstream_reference"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
        )
        return platform.add_route(item, scope(payload)).to_dict()

    def create_version(payload: dict[str, Any]) -> dict[str, Any]:
        item = ApiVersion(
            str(payload["id"]),
            str(payload["api_id"]),
            str(payload["semantic_version"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            bool(payload.get("active", False)),
            bool(payload.get("default", False)),
            compatibility=str(payload.get("compatibility", "backward-compatible")),
            migration_notes=str(payload.get("migration_notes", "")),
        )
        return platform.add_version(item, scope(payload)).to_dict()

    def create_policy(payload: dict[str, Any]) -> dict[str, Any]:
        item = Policy(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["kind"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            payload.get("api_id"),
            payload.get("route_id"),
            dict(payload.get("configuration", {})),
        )
        return platform.add_policy(item, scope(payload)).to_dict()

    def create_credential(payload: dict[str, Any]) -> dict[str, Any]:
        item = Credential(
            str(payload["id"]),
            str(payload["kind"]),
            str(payload["secret_reference"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["consumer"]),
            frozenset(payload.get("scopes", ())),
        )
        return platform.add_credential(item, scope(payload)).to_dict()

    def create_subscription(payload: dict[str, Any]) -> dict[str, Any]:
        quota = Quota(**dict(payload.get("quota", {})))
        item = Subscription(
            str(payload["id"]),
            str(payload["api_id"]),
            str(payload["consumer"]),
            str(payload["application"]),
            str(payload["plan"]),
            frozenset(payload.get("entitlements", ())),
            quota,
            str(payload["tenant"]),
            str(payload["workspace"]),
            SubscriptionStatus(str(payload.get("status", "pending"))),
        )
        return platform.subscribe(item, scope(payload)).to_dict()

    def collection(name: str) -> Any:
        def endpoint(
            tenant: str,
            workspace: str,
            actor: str = "api",
            permissions: str = "api-management:read",
        ) -> dict[str, Any]:
            current = scope(
                tenant=tenant,
                workspace=workspace,
                actor=actor,
                permissions=permissions,
            )
            return listed(
                platform.list_apis(current)
                if name == "apis"
                else platform._scoped(getattr(platform, name).values(), current)
            )

        return endpoint

    endpoints = {
        "/apis": ("apis", create_api),
        "/gateways": ("gateways", create_gateway),
        "/routes": ("routes", create_route),
        "/versions": ("versions", create_version),
        "/policies": ("policies", create_policy),
        "/keys": ("credentials", create_credential),
        "/tokens": ("credentials", create_credential),
        "/subscriptions": ("subscriptions", create_subscription),
    }
    for path, (name, create) in endpoints.items():
        add(path, collection(name), ["GET"])
        add(path, create, ["POST"])

    def configuration(name: str) -> Any:
        def endpoint(
            tenant: str,
            workspace: str,
            actor: str = "api",
            permissions: str = "api-management:read",
        ) -> dict[str, Any]:
            current = scope(
                tenant=tenant,
                workspace=workspace,
                actor=actor,
                permissions=permissions,
            )
            data = platform._configuration(getattr(platform, name), current)
            return {"data": data, "total": len(data), "error": None}

        return endpoint

    add("/quotas", configuration("quotas"), ["GET"])
    add("/rate-limits", configuration("rate_limits"), ["GET"])

    def set_quota(payload: dict[str, Any]) -> dict[str, Any]:
        item = platform.set_quota(
            str(payload["target"]), Quota(**dict(payload["quota"])), scope(payload)
        )
        return asdict(item)

    def set_rate_limit(payload: dict[str, Any]) -> dict[str, Any]:
        item = platform.set_rate_limit(
            str(payload["target"]),
            RateLimit(**dict(payload["rate_limit"])),
            scope(payload),
        )
        return asdict(item)

    add("/quotas", set_quota, ["POST"])
    add("/rate-limits", set_rate_limit, ["POST"])
    add(
        "/analytics",
        lambda tenant, workspace, actor="api", permissions="api-management:read": {
            "data": platform.dashboard(
                scope(
                    tenant=tenant,
                    workspace=workspace,
                    actor=actor,
                    permissions=permissions,
                )
            )["analytics"],
            "error": None,
        },
        ["GET"],
    )
    add(
        "/developer-portal",
        lambda tenant, workspace, actor="api", permissions="api-management:read": (
            platform.developer_portal(
                scope(
                    tenant=tenant,
                    workspace=workspace,
                    actor=actor,
                    permissions=permissions,
                )
            )
        ),
        ["GET"],
    )
    add(
        "/dashboard",
        lambda tenant, workspace, actor="api", permissions="api-management:read": (
            platform.dashboard(
                scope(
                    tenant=tenant,
                    workspace=workspace,
                    actor=actor,
                    permissions=permissions,
                )
            )
        ),
        ["GET"],
    )
    add("/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("register_api_management_routes",)
