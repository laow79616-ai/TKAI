"""HTTP route registration for the TikTok AI Operations Planner."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import ObjectiveKind, PlannerScope, StrategyKind
from ..service import TikTokAIOperationsPlanner

RESOURCE_NAMES = (
    "plans",
    "objectives",
    "strategies",
    "constraints",
    "resources",
    "schedules",
    "recommendations",
    "simulations",
    "approvals",
    "executions",
    "reviews",
    "history",
    "analytics",
)
ROUTES = tuple(f"/tiktok/operations-planner/{name}" for name in RESOURCE_NAMES)


def register_operations_planner_routes(
    app: Any, service: TikTokAIOperationsPlanner
) -> None:
    def scope() -> PlannerScope:
        return PlannerScope(
            "default", "default", "api", frozenset({"tiktok:planner:admin"})
        )

    def serialized(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope())]

    readers = {
        ROUTES[0]: lambda: [
            item.to_dict()
            for item in service.scoped_values(service.plans.values(), scope())
        ],
        ROUTES[1]: lambda: {"objectives": [item.value for item in ObjectiveKind]},
        ROUTES[2]: lambda: {"strategies": [item.value for item in StrategyKind]},
        ROUTES[3]: lambda: {
            "constraints": [
                asdict(bound)
                for plan in service.scoped_values(service.plans.values(), scope())
                for bound in plan.constraints
            ]
        },
        ROUTES[4]: lambda: {"resources": service.snapshots.get("resources", {})},
        ROUTES[5]: lambda: {
            "schedules": [
                asdict(item)
                for item in service.scoped_values(
                    service.recommendations.values(), scope()
                )
            ]
        },
        ROUTES[6]: lambda: serialized(service.recommendations.values()),
        ROUTES[7]: lambda: serialized(service.simulations.values()),
        ROUTES[8]: lambda: serialized(service.approvals.values()),
        ROUTES[9]: lambda: serialized(service.executions.values()),
        ROUTES[10]: lambda: serialized(service.reviews.values()),
        ROUTES[11]: lambda: serialized(service.history),
        ROUTES[12]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-operations-planner"]
        )
    app.add_api_route(
        "/tiktok/operations-planner/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-operations-planner"],
    )
    app.add_api_route(
        "/tiktok/operations-planner/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-operations-planner"],
    )
