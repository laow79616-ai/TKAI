"""HTTP route registration for the TikTok Automation Engine."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import AutomationScope
from ..service import TikTokAutomationEngine

ROUTES = (
    "/tiktok/automation",
    "/tiktok/automation/plans",
    "/tiktok/automation/executions",
    "/tiktok/automation/triggers",
    "/tiktok/automation/conditions",
    "/tiktok/automation/queues",
    "/tiktok/automation/recovery",
    "/tiktok/automation/analytics",
)


def register_automation_routes(app: Any, service: TikTokAutomationEngine) -> None:
    def scope() -> AutomationScope:
        return AutomationScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:automation:admin"}),
        )

    def scoped(values: Any) -> list[dict[str, Any]]:
        request_scope = scope()
        return [
            asdict(item)
            for item in values
            if item.tenant == request_scope.tenant
            and item.workspace == request_scope.workspace
        ]

    endpoints = {
        ROUTES[0]: lambda: [
            item.to_dict() for item in service.list_automations(scope())
        ],
        ROUTES[1]: lambda: scoped(service.plans.values()),
        ROUTES[2]: lambda: scoped(service.executions.values()),
        ROUTES[3]: lambda: scoped(service.triggers.values()),
        ROUTES[4]: lambda: scoped(service.conditions.values()),
        ROUTES[5]: lambda: service.queue_health(scope()),
        ROUTES[6]: lambda: scoped(
            item for item in service.executions.values() if item.recovery_count
        ),
        ROUTES[7]: lambda: service.analytics(scope()),
    }
    for path, endpoint in endpoints.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-automation"])
    app.add_api_route(
        "/tiktok/automation/monitoring",
        lambda: service.monitoring(scope()),
        methods=["GET"],
        tags=["tiktok-automation"],
    )
    app.add_api_route(
        "/tiktok/automation/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-automation"],
    )
    app.add_api_route(
        "/tiktok/automation/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-automation"],
    )
