"""HTTP routes for the TikTok Operations Command Center."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..adapters import MODULES
from ..models import ActionKind, OperationsScope
from ..service import TikTokOperationsCommandCenter

ROUTES = tuple(
    f"/tiktok/operations/{name}"
    for name in (
        "overview",
        "accounts",
        "browsers",
        "proxies",
        "tasks",
        "alerts",
        "incidents",
        "health",
        "recovery",
        "activity",
        "audit",
        "actions",
    )
)


def register_operations_center_routes(
    app: Any, service: TikTokOperationsCommandCenter
) -> None:
    def scope() -> OperationsScope:
        return OperationsScope(
            "default", "default", "api", frozenset({"tiktok:operations:admin"})
        )

    def serialized(values: Any) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(values, scope())]

    readers = {
        ROUTES[0]: lambda: service.overview(scope()),
        ROUTES[1]: lambda: service.ports["accounts"].status(scope()),
        ROUTES[2]: lambda: service.ports["browsers"].status(scope()),
        ROUTES[3]: lambda: service.ports["proxies"].status(scope()),
        ROUTES[4]: lambda: serialized(service.tasks.values()),
        ROUTES[5]: lambda: serialized(service.alerts.values()),
        ROUTES[6]: lambda: serialized(service.incidents.values()),
        ROUTES[7]: lambda: asdict(service.health(scope())),
        ROUTES[8]: lambda: serialized(service.recoveries.values()),
        ROUTES[9]: lambda: serialized(service.activity),
        ROUTES[10]: lambda: serialized(service.audit),
        ROUTES[11]: lambda: {
            "actions": [item.value for item in service_action_kinds()]
        },
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-operations-center"]
        )
    for name in MODULES[3:]:
        app.add_api_route(
            f"/tiktok/operations/{name}",
            lambda module=name: service.ports[module].status(scope()),
            methods=["GET"],
            tags=["tiktok-operations-center"],
        )
    app.add_api_route(
        "/tiktok/operations/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-operations-center"],
    )
    app.add_api_route(
        "/tiktok/operations/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-operations-center"],
    )

    def execute_action(payload: dict[str, Any]) -> dict[str, Any]:
        return service.execute_action(
            ActionKind(str(payload["action"])),
            str(payload["resource_reference"]),
            str(payload["module"]),
            str(payload["reason"]),
            str(payload["correlation_id"]),
            scope(),
        )

    app.add_api_route(
        "/tiktok/operations/actions",
        execute_action,
        methods=["POST"],
        tags=["tiktok-operations-center"],
    )


def service_action_kinds() -> Any:
    return ActionKind
