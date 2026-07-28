"""Framework-neutral TikTok Account Center API routes."""

from typing import Any

from ..models import AccountScope, LoginMethod, TikTokAccount, TikTokProfile
from ..service import TikTokAccountCenter

ROUTES = (
    "/tiktok/accounts",
    "/tiktok/login",
    "/tiktok/groups",
    "/tiktok/tags",
    "/tiktok/cookies",
    "/tiktok/sessions",
    "/tiktok/status",
    "/tiktok/risk",
)


def register_tiktok_routes(app: Any, center: TikTokAccountCenter) -> None:
    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "tiktok:read",
    ) -> AccountScope:
        return AccountScope(tenant, workspace, actor, frozenset(permissions.split(",")))

    def listing(tenant: str, workspace: str, query: str = "") -> dict[str, Any]:
        items = center.search(scope(tenant, workspace), query=query)
        return {
            "data": [i.to_dict() for i in items],
            "total": len(items),
            "error": None,
        }

    def create(payload: dict[str, Any]) -> dict[str, Any]:
        s = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "tiktok:write")),
        )
        return center.create(
            TikTokAccount(
                str(payload["id"]),
                s.tenant,
                s.workspace,
                TikTokProfile(**dict(payload.get("profile", {}))),
            ),
            s,
        ).to_dict()

    def login(payload: dict[str, Any]) -> dict[str, Any]:
        s = scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "tiktok:login")),
        )
        return center.login(
            str(payload["account_id"]),
            LoginMethod(str(payload["method"])),
            str(payload.get("state", "")),
            s,
        ).to_dict()

    def dashboard(tenant: str, workspace: str) -> dict[str, Any]:
        return center.dashboard(scope(tenant, workspace))

    app.add_api_route(ROUTES[0], listing, methods=["GET"], tags=["tiktok"])
    app.add_api_route(ROUTES[0], create, methods=["POST"], tags=["tiktok"])
    app.add_api_route(ROUTES[1], login, methods=["POST"], tags=["tiktok"])
    for path in ROUTES[2:]:
        app.add_api_route(path, dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route("/tiktok/dashboard", dashboard, methods=["GET"], tags=["tiktok"])
    app.add_api_route(
        "/tiktok/metrics",
        center.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok"],
    )
