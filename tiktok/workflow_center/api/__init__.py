"""HTTP route registration for TikTok Workflow Orchestration Center."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from ..models import WorkflowScope
from ..service import TikTokWorkflowOrchestrationCenter

ROUTES = (
    "/tiktok/workflows",
    "/tiktok/workflows/templates",
    "/tiktok/workflows/executions",
    "/tiktok/workflows/queues",
    "/tiktok/workflows/schedules",
    "/tiktok/workflows/history",
    "/tiktok/workflows/analytics",
)


def register_workflow_center_routes(
    app: Any, service: TikTokWorkflowOrchestrationCenter
) -> None:
    def scope() -> WorkflowScope:
        return WorkflowScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:workflow:admin"}),
        )

    def scoped(values: Any) -> list[dict[str, Any]]:
        request_scope = scope()
        return [
            asdict(item)
            for item in values
            if item.tenant == request_scope.tenant
            and item.workspace == request_scope.workspace
        ]

    readers: dict[str, Callable[[], Any]] = {
        ROUTES[0]: lambda: [item.to_dict() for item in service.list_workflows(scope())],
        ROUTES[1]: lambda: scoped(service.templates.values()),
        ROUTES[2]: lambda: scoped(service.executions.values()),
        ROUTES[3]: lambda: service.queue_metrics(scope()),
        ROUTES[4]: lambda: scoped(service.schedules.values()),
        ROUTES[5]: lambda: scoped(service.history),
        ROUTES[6]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-workflow-center"]
        )
    app.add_api_route(
        "/tiktok/workflows/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-workflow-center"],
    )
    app.add_api_route(
        "/tiktok/workflows/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-workflow-center"],
    )
