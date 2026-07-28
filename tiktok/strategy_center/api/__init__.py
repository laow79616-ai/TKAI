"""HTTP API for the advisory TikTok Autonomous Strategy Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import ObjectiveType, OptionType, StrategyScope
from ..service import TikTokAutonomousStrategyCenter

RESOURCE_NAMES = (
    "strategies",
    "objectives",
    "contexts",
    "constraints",
    "options",
    "evaluations",
    "scenarios",
    "recommendations",
    "approvals",
    "handoffs",
    "reviews",
    "history",
    "analytics",
)
ROUTES = tuple(f"/tiktok/strategy-center/{name}" for name in RESOURCE_NAMES)


def register_strategy_center_routes(
    app: Any, service: TikTokAutonomousStrategyCenter
) -> None:
    def scope() -> StrategyScope:
        return StrategyScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:strategy-center:admin"}),
        )

    def serialized(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope())]

    readers = {
        ROUTES[0]: lambda: [
            item.to_dict()
            for item in service.scoped_values(service.strategies.values(), scope())
        ],
        ROUTES[1]: lambda: {"objectives": [item.value for item in ObjectiveType]},
        ROUTES[2]: lambda: serialized(service.contexts.values()),
        ROUTES[3]: lambda: {
            "constraints": [
                asdict(bound)
                for strategy in service.scoped_values(
                    service.strategies.values(), scope()
                )
                for bound in strategy.constraints
            ]
        },
        ROUTES[4]: lambda: {
            "option_types": [item.value for item in OptionType],
            "items": serialized(service.options.values()),
        },
        ROUTES[5]: lambda: serialized(service.evaluations.values()),
        ROUTES[6]: lambda: serialized(service.scenarios.values()),
        ROUTES[7]: lambda: serialized(service.recommendations.values()),
        ROUTES[8]: lambda: serialized(service.approvals.values()),
        ROUTES[9]: lambda: serialized(service.handoffs.values()),
        ROUTES[10]: lambda: serialized(service.reviews.values()),
        ROUTES[11]: lambda: serialized(service.history),
        ROUTES[12]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-strategy-center"]
        )
    app.add_api_route(
        "/tiktok/strategy-center/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-strategy-center"],
    )
    app.add_api_route(
        "/tiktok/strategy-center/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-strategy-center"],
        include_in_schema=False,
    )
