"""Transport-neutral API registration for the TikTok Runtime Manager."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import RuntimeScope
from ..service import TikTokRuntimeManager

RESOURCE_NAMES = (
    "services",
    "processes",
    "workers",
    "registry",
    "health",
    "recovery",
    "statistics",
)
ROUTES = ("/tiktok/runtime",) + tuple(
    f"/tiktok/runtime/{name}" for name in RESOURCE_NAMES
)


def register_runtime_manager_routes(app: Any, service: TikTokRuntimeManager) -> None:
    def scope() -> RuntimeScope:
        return RuntimeScope(
            service.runtime.tenant,
            service.runtime.workspace,
            "api",
            frozenset({"tiktok:runtime:admin"}),
        )

    handlers = {
        "/tiktok/runtime": lambda: asdict(service.runtime),
        "/tiktok/runtime/services": lambda: [
            asdict(item) for item in service.services.values()
        ],
        "/tiktok/runtime/processes": lambda: [
            asdict(item) for item in service.processes.values()
        ],
        "/tiktok/runtime/workers": lambda: [
            asdict(item) for item in service.workers.values()
        ],
        "/tiktok/runtime/registry": lambda: {
            key: {
                "capabilities": sorted(value.capabilities),
                "dependencies": sorted(value.dependencies),
                "version": value.version,
                "health": value.health.value,
                "heartbeat": value.heartbeat_at,
            }
            for key, value in service.services.items()
        },
        "/tiktok/runtime/health": lambda: service.health(scope()),
        "/tiktok/runtime/recovery": lambda: dict(service.recovery_attempts),
        "/tiktok/runtime/statistics": lambda: service.statistics(scope()),
    }
    for path in ROUTES:
        app.add_api_route(
            path,
            handlers[path],
            methods=["GET"],
            tags=["tiktok-runtime-manager"],
        )
    app.add_api_route(
        "/tiktok/runtime/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-runtime-manager"],
    )
    app.add_api_route(
        "/tiktok/runtime/telemetry",
        lambda: service.telemetry(scope()),
        methods=["GET"],
        tags=["tiktok-runtime-manager"],
    )
    app.add_api_route(
        "/tiktok/runtime/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-runtime-manager"],
    )
