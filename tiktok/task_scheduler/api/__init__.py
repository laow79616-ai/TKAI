"""Transport-neutral HTTP registration for the TikTok AI Task Scheduler."""

from __future__ import annotations

from dataclasses import asdict
from enum import Enum
from typing import Any

from ..models import SchedulerScope
from ..service import TikTokAITaskScheduler

RESOURCE_NAMES = (
    "tasks",
    "queues",
    "schedules",
    "dependencies",
    "allocations",
    "workers",
    "executions",
    "checkpoints",
    "retries",
    "failures",
    "recovery",
    "limits",
    "telemetry",
    "statistics",
)
ROUTES = tuple(f"/tiktok/task-scheduler/{name}" for name in RESOURCE_NAMES)


def _serializable(item: Any) -> Any:
    if isinstance(item, Enum):
        return item.value
    if hasattr(item, "isoformat"):
        return item.isoformat()
    raise TypeError


def register_task_scheduler_routes(app: Any, service: TikTokAITaskScheduler) -> None:
    def scope() -> SchedulerScope:
        return SchedulerScope(
            "default", "default", "api", frozenset({"tiktok:scheduler:admin"})
        )

    def values(store: dict[str, Any]) -> list[dict[str, Any]]:
        return [asdict(item) for item in service.scoped_values(store.values(), scope())]

    handlers = {
        "tasks": lambda: values(service.tasks),
        "queues": lambda: {key: list(value) for key, value in service.queues.items()},
        "schedules": lambda: [
            {"task_id": item.id, "schedule": asdict(item.schedule)}
            for item in service.scoped_values(service.tasks.values(), scope())
        ],
        "dependencies": lambda: {
            key: [asdict(value) for value in items]
            for key, items in service.dependencies.items()
        },
        "allocations": lambda: values(service.allocations),
        "workers": lambda: [asdict(item) for item in service.workers.values()],
        "executions": lambda: values(service.executions),
        "checkpoints": lambda: values(service.checkpoints),
        "retries": lambda: [
            asdict(item)
            for item in service.scoped_values(service.tasks.values(), scope())
            if item.status.value == "retrying"
        ],
        "failures": lambda: values(service.failures),
        "recovery": lambda: dict(service.recovery_attempts),
        "limits": lambda: asdict(service.limits),
        "telemetry": lambda: service.telemetry(scope()),
        "statistics": lambda: service.statistics(scope()),
    }
    for name, path in zip(RESOURCE_NAMES, ROUTES, strict=True):
        app.add_api_route(
            path, handlers[name], methods=["GET"], tags=["tiktok-ai-task-scheduler"]
        )
    app.add_api_route(
        "/tiktok/task-scheduler/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-ai-task-scheduler"],
    )
    app.add_api_route(
        "/tiktok/task-scheduler/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-ai-task-scheduler"],
    )
