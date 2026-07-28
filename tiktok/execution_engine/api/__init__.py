"""HTTP route registration for the TikTok AI Execution Engine."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import ExecutionScope
from ..service import TikTokAIExecutionEngine

ROUTES = (
    "/tiktok/execution/plans",
    "/tiktok/execution/pipelines",
    "/tiktok/execution/stages",
    "/tiktok/execution/checkpoints",
    "/tiktok/execution/results",
    "/tiktok/execution/monitoring",
    "/tiktok/execution/analytics",
)


def register_execution_routes(app: Any, service: TikTokAIExecutionEngine) -> None:
    def scope() -> ExecutionScope:
        return ExecutionScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:execution:admin"}),
        )

    def serialized(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope())]

    readers = {
        ROUTES[0]: lambda: [
            item.to_dict()
            for item in service.scoped_values(service.plans.values(), scope())
        ],
        ROUTES[1]: lambda: serialized(service.pipelines.values()),
        ROUTES[2]: lambda: serialized(service.stages.values()),
        ROUTES[3]: lambda: serialized(service.checkpoints.values()),
        ROUTES[4]: lambda: serialized(service.results.values()),
        ROUTES[5]: lambda: service.monitoring(scope()),
        ROUTES[6]: lambda: service.analytics(scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-execution"])
    app.add_api_route(
        "/tiktok/execution/verification",
        lambda: serialized(service.verifications.values()),
        methods=["GET"],
        tags=["tiktok-execution"],
    )
    app.add_api_route(
        "/tiktok/execution/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-execution"],
    )
    app.add_api_route(
        "/tiktok/execution/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-execution"],
    )
