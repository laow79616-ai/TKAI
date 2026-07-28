"""HTTP API for the Enterprise TikTok Autonomous Mission Engine."""

from __future__ import annotations

from typing import Any

from ..models import MissionScope
from ..service import TikTokAutonomousMissionEngine

ROUTES = (
    "/tiktok/mission-engine/missions",
    "/tiktok/mission-engine/dispatch",
    "/tiktok/mission-engine/recovery",
    "/tiktok/mission-engine/analytics",
)


def register_mission_engine_routes(
    app: Any, service: TikTokAutonomousMissionEngine
) -> None:
    def scope() -> MissionScope:
        return MissionScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:mission-engine:admin"}),
        )

    app.add_api_route(
        ROUTES[0],
        lambda: [item.to_dict() for item in service.queue(scope())],
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
    app.add_api_route(
        ROUTES[1],
        lambda: [
            {"mission_id": item.id, "worker": item.worker, "queue": item.queue}
            for item in service.queue(scope())
            if item.worker
        ],
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
    app.add_api_route(
        ROUTES[2],
        lambda: [
            item.to_dict()
            for item in service.queue(scope())
            if item.state.value in {"recovering", "rolled_back"}
        ],
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
    app.add_api_route(
        ROUTES[3],
        lambda: service.analytics(scope()),
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
    app.add_api_route(
        "/tiktok/mission-engine/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
    app.add_api_route(
        "/tiktok/mission-engine/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-mission-engine"],
    )
