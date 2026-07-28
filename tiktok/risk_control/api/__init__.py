"""HTTP route registration for Risk Control Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RiskScope
from ..service import TikTokRiskControlCenter

ROUTES = tuple(
    f"/tiktok/risk-control/{name}"
    for name in (
        "profiles",
        "policies",
        "rules",
        "signals",
        "scores",
        "events",
        "alerts",
        "restrictions",
        "limits",
        "pauses",
        "reviews",
        "recovery",
        "health",
        "analytics",
    )
)


def register_risk_control_routes(app: Any, service: TikTokRiskControlCenter) -> None:
    def scope() -> RiskScope:
        return RiskScope("default", "default", "api", frozenset({"tiktok:risk:admin"}))

    def scoped(values: Any) -> list[Any]:
        request_scope = scope()
        return [
            asdict(value)
            for value in values
            if value.tenant == request_scope.tenant
            and value.workspace == request_scope.workspace
        ]

    readers = {
        ROUTES[0]: lambda: [p.to_dict() for p in service.list_profiles(scope())],
        ROUTES[1]: lambda: scoped(service.policies.values()),
        ROUTES[2]: lambda: scoped(service.rules.values()),
        ROUTES[3]: lambda: scoped(service.signals.values()),
        ROUTES[4]: lambda: {
            key: [asdict(value) for value in values]
            for key, values in service.scores.items()
            if key in {profile.id for profile in service.list_profiles(scope())}
        },
        ROUTES[5]: lambda: [
            event
            for event in service.events
            if event["tenant"] == scope().tenant
            and event["workspace"] == scope().workspace
        ],
        ROUTES[6]: lambda: scoped(service.alerts.values()),
        ROUTES[7]: lambda: scoped(service.restrictions.values()),
        ROUTES[8]: lambda: scoped(service.limits.values()),
        ROUTES[9]: lambda: scoped(service.pauses.values()),
        ROUTES[10]: lambda: scoped(service.reviews.values()),
        ROUTES[11]: lambda: scoped(service.recoveries.values()),
        ROUTES[12]: lambda: scoped(service.health.values()),
        ROUTES[13]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-risk-control"])
    app.add_api_route(
        "/tiktok/risk-control/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-risk-control"],
    )
    app.add_api_route(
        "/tiktok/risk-control/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-risk-control"],
    )
