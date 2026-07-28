"""HTTP route registration for TikTok account farming."""

from __future__ import annotations

from typing import Any

from ..models import FarmingScope
from ..service import TikTokAccountFarming

ROUTES = (
    "/tiktok/account-farming/plans",
    "/tiktok/account-farming/profiles",
    "/tiktok/account-farming/schedules",
    "/tiktok/account-farming/approvals",
    "/tiktok/account-farming/executions",
    "/tiktok/account-farming/signals",
    "/tiktok/account-farming/risks",
    "/tiktok/account-farming/recommendations",
    "/tiktok/account-farming/analytics",
)


def _scope() -> FarmingScope:
    return FarmingScope(
        "default",
        "default",
        "api",
        frozenset({"tiktok:farming:admin"}),
    )


def register_account_farming_routes(app: Any, service: TikTokAccountFarming) -> None:
    """Register bounded collection endpoints without global service state."""

    readers = {
        ROUTES[0]: lambda: [item.to_dict() for item in service.list_plans(_scope())],
        ROUTES[1]: lambda: list(service.profiles.values()),
        ROUTES[2]: lambda: list(service.schedules.values()),
        ROUTES[3]: lambda: list(service.approvals.values()),
        ROUTES[4]: lambda: list(service.executions.values()),
        ROUTES[5]: lambda: list(service.signals),
        ROUTES[6]: lambda: list(service.risks.values()),
        ROUTES[7]: lambda: list(service.recommendations.values()),
        ROUTES[8]: lambda: service.analytics(_scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-account-farming"]
        )
    app.add_api_route(
        "/tiktok/account-farming/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-account-farming"],
    )
    app.add_api_route(
        "/tiktok/account-farming/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-account-farming"],
    )
