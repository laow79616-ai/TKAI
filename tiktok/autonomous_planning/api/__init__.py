"""GET-only API for the TikTok Autonomous Planning Center."""

from __future__ import annotations

from typing import Any

from ..models import PlanningContext
from ..service import RESOURCE_NAMES, TikTokAutonomousPlanningCenter

BASE_PATH = "/tiktok/autonomous-planning"
ROUTES = tuple(f"{BASE_PATH}/{name}" for name in RESOURCE_NAMES) + (
    f"{BASE_PATH}/history",
    f"{BASE_PATH}/analytics",
)


def register_autonomous_planning_routes(
    app: Any, service: TikTokAutonomousPlanningCenter
) -> None:
    def context() -> PlanningContext:
        return PlanningContext(
            "default", "default", "api", frozenset({"tiktok:autonomous-planning:read"})
        )

    for name in RESOURCE_NAMES:
        store = getattr(service, name)

        def endpoint(store: dict[str, object] = store) -> list[dict[str, object]]:
            return service.items(store, context())

        app.add_api_route(
            f"{BASE_PATH}/{name}",
            endpoint,
            methods=["GET"],
            tags=["tiktok-autonomous-planning"],
        )
    app.add_api_route(
        f"{BASE_PATH}/history",
        lambda: service.get_history(context()),
        methods=["GET"],
        tags=["tiktok-autonomous-planning"],
    )
    app.add_api_route(
        f"{BASE_PATH}/analytics",
        lambda: service.analytics(context()),
        methods=["GET"],
        tags=["tiktok-autonomous-planning"],
    )
    app.add_api_route(
        f"{BASE_PATH}/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-autonomous-planning"],
    )
    app.add_api_route(
        f"{BASE_PATH}/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-autonomous-planning"],
    )
