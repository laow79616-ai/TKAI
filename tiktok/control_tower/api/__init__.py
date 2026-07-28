"""HTTP routes for the TikTok AI Control Tower."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import ControlTowerScope
from ..service import TikTokAIControlTower

ROUTES = (
    "/tiktok/control-tower/overview",
    "/tiktok/control-tower/runtime",
    "/tiktok/control-tower/resources",
    "/tiktok/control-tower/automation",
    "/tiktok/control-tower/execution",
    "/tiktok/control-tower/recovery",
    "/tiktok/control-tower/risk",
    "/tiktok/control-tower/analytics",
    "/tiktok/control-tower/activity",
)


def register_control_tower_routes(app: Any, service: TikTokAIControlTower) -> None:
    def scope() -> ControlTowerScope:
        return ControlTowerScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:control-tower:admin"}),
        )

    readers = {
        ROUTES[0]: lambda: service.overview(scope()),
        ROUTES[1]: lambda: service.module("runtime", scope()),
        ROUTES[2]: lambda: service.module("resources", scope()),
        ROUTES[3]: lambda: service.module("automation", scope()),
        ROUTES[4]: lambda: service.module("execution", scope()),
        ROUTES[5]: lambda: service.module("recovery", scope()),
        ROUTES[6]: lambda: service.module("risk", scope()),
        ROUTES[7]: lambda: service.module("analytics", scope()),
        ROUTES[8]: lambda: [asdict(item) for item in service.scoped_activity(scope())],
        "/tiktok/control-tower/topology": lambda: service.topology(scope()),
        "/tiktok/control-tower/alerts": lambda: [
            asdict(item) for item in service.scoped_alerts(scope())
        ],
        "/tiktok/control-tower/dashboard": lambda: service.dashboard(scope()),
        "/tiktok/control-tower/metrics": service.metrics.render_prometheus,
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-control-tower"]
        )
