"""HTTP routes for the TikTok Autonomous Operation Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import OperationScope
from ..service import TikTokAutonomousOperationCenter

ROUTES = (
    "/tiktok/autonomous-operation/missions",
    "/tiktok/autonomous-operation/plans",
    "/tiktok/autonomous-operation/execution",
    "/tiktok/autonomous-operation/recovery",
    "/tiktok/autonomous-operation/analytics",
)


def register_autonomous_operation_routes(
    app: Any, service: TikTokAutonomousOperationCenter
) -> None:
    def scope() -> OperationScope:
        return OperationScope(
            "default", "default", "api", frozenset({"tiktok:autonomous:admin"})
        )

    readers = {
        ROUTES[0]: lambda: [
            item.to_dict()
            for item in service.scoped_values(service.missions.values(), scope())
        ],
        ROUTES[1]: lambda: [
            asdict(item)
            for item in service.scoped_values(service.plans.values(), scope())
        ],
        ROUTES[2]: lambda: [
            asdict(item)
            for item in service.scoped_values(service.executions.values(), scope())
        ],
        ROUTES[3]: lambda: [
            asdict(item)
            for item in service.scoped_values(service.executions.values(), scope())
            if item.recovery_state != "idle"
        ],
        ROUTES[4]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-autonomous-operation"]
        )
    app.add_api_route(
        "/tiktok/autonomous-operation/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-autonomous-operation"],
    )
    app.add_api_route(
        "/tiktok/autonomous-operation/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-autonomous-operation"],
    )
