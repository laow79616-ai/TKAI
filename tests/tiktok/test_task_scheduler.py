from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from typing import Any

import pytest

from tiktok.task_scheduler import (
    DependencyRequirement,
    Priority,
    RetryPolicy,
    Schedule,
    ScheduledTask,
    ScheduleKind,
    SchedulerLimits,
    SchedulerScope,
    TaskDependency,
    TaskStatus,
    TaskType,
    TikTokAITaskScheduler,
    Worker,
)
from tiktok.task_scheduler.api import ROUTES, register_task_scheduler_routes
from tiktok.task_scheduler.metrics import METRIC_NAMES
from tiktok.task_scheduler.models import utcnow


def scope(workspace: str = "w1") -> SchedulerScope:
    return SchedulerScope(
        "tenant-1", workspace, "operator", frozenset({"tiktok:scheduler:admin"})
    )


def task(
    reference: str,
    task_type: TaskType = TaskType.DIAGNOSTICS,
    workspace: str = "w1",
    **kwargs: Any,
) -> ScheduledTask:
    return ScheduledTask(
        reference,
        f"Task {reference}",
        "bounded test task",
        task_type,
        "tenant-1",
        workspace,
        "owner",
        **kwargs,
    )


def ready(service: TikTokAITaskScheduler, item: ScheduledTask) -> ScheduledTask:
    service.create_task(item, scope(item.workspace))
    return service.transition(item.id, TaskStatus.READY, scope(item.workspace))


def test_task_crud_lifecycle_rbac_isolation_and_secret_safety() -> None:
    service = TikTokAITaskScheduler()
    item = service.create_task(task("t1"), scope())
    assert (
        service.transition(item.id, TaskStatus.PENDING_APPROVAL, scope()).version == 2
    )
    assert service.approve(item.id, "approval://1", scope()).status is TaskStatus.READY
    service.enqueue(item.id, scope())
    assert item.status is TaskStatus.QUEUED
    with pytest.raises(PermissionError):
        service.transition(item.id, TaskStatus.PAUSED, scope("other"))
    with pytest.raises(ValueError):
        service.create_task(task("bad", payload={"cookie": "plaintext"}), scope())
    with pytest.raises(ValueError):
        service.create_task(task("code", payload={"command": "whoami"}), scope())
    with pytest.raises(ValueError):
        service.create_task(task("custom", TaskType.CUSTOM_BOUNDED), scope())


def test_schedule_priority_aging_dependencies_and_cycle_detection() -> None:
    service = TikTokAITaskScheduler()
    parent = ready(service, task("parent"))
    child = ready(
        service,
        task(
            "child",
            priority=Priority.HIGH,
            schedule=Schedule(
                ScheduleKind.INTERVAL, interval_seconds=60, maximum_runs=5
            ),
        ),
    )
    service.add_dependency(
        TaskDependency(child.id, parent.id, DependencyRequirement.SUCCESS), scope()
    )
    with pytest.raises(RuntimeError):
        service.enqueue(child.id, scope())
    with pytest.raises(ValueError):
        service.add_dependency(TaskDependency(parent.id, child.id), scope())
    parent.status = TaskStatus.COMPLETED
    child.created_at = utcnow() - timedelta(hours=8)
    service.enqueue(child.id, scope())
    assert service._effective_priority(child) == 100


def test_fair_bounded_worker_allocation_execution_release_and_metrics() -> None:
    service = TikTokAITaskScheduler()
    normal = ready(service, task("normal", priority=Priority.NORMAL))
    critical = ready(service, task("critical", priority=Priority.CRITICAL))
    service.register_worker(
        Worker("worker-1", "local", 1, frozenset(TaskType), "w1"), scope()
    )
    service.enqueue(normal.id, scope())
    service.enqueue(critical.id, scope())
    execution = service.dispatch_next(scope())
    assert execution is not None and execution.task_id == critical.id
    result = service.execute(execution.id, scope())
    assert result.status is TaskStatus.COMPLETED
    assert result.outcome["bounded"] is True
    assert service.workers["worker-1"].current_load == 0
    assert service.metrics.values["tiktok_scheduler_completed_total"] == 1


def test_approval_risk_cancellation_kill_switch_and_restriction_awareness() -> None:
    service = TikTokAITaskScheduler()
    publishing = ready(service, task("publish", TaskType.PUBLISHING_JOB))
    service.register_worker(
        Worker("publisher", "local", 1, frozenset({TaskType.PUBLISHING_JOB}), "w1"),
        scope(),
    )
    service.enqueue(publishing.id, scope())
    execution = service.dispatch_next(scope())
    assert execution is not None
    assert service.execute(execution.id, scope()).status is TaskStatus.FAILED
    restricted = ready(
        service,
        task("restricted", metadata={"restriction_active": True}),
    )
    service.register_worker(
        Worker("diagnostic", "local", 1, frozenset({TaskType.DIAGNOSTICS}), "w1"),
        scope(),
    )
    service.enqueue(restricted.id, scope())
    restricted_execution = service.dispatch_next(scope())
    assert restricted_execution is not None
    assert service.execute(restricted_execution.id, scope()).status is TaskStatus.FAILED
    service.set_pause(scope(), kill_switch=True)
    assert service.dispatch_next(scope()) is None
    service.set_pause(scope(), kill_switch=False, workspace=True)
    paused = ready(service, task("paused"))
    with pytest.raises(RuntimeError):
        service.enqueue(paused.id, scope())


def test_checkpoints_resume_retries_dead_letter_and_integrity() -> None:
    class FailingPort:
        def preflight(self, item: ScheduledTask, request_scope: SchedulerScope) -> None:
            return None

        def execute(
            self, item: ScheduledTask, request_scope: SchedulerScope
        ) -> dict[str, Any]:
            raise RuntimeError("bounded failure")

    service = TikTokAITaskScheduler(
        {"operations": FailingPort()},
        SchedulerLimits(maximum_retry_attempts=2),
    )
    item = ready(
        service,
        task(
            "retry", retry_policy=RetryPolicy(maximum_attempts=2, retry_delay_seconds=0)
        ),
    )
    service.register_worker(
        Worker("worker", "local", 1, frozenset({TaskType.DIAGNOSTICS}), "w1"), scope()
    )
    service.enqueue(item.id, scope())
    execution = service.dispatch_next(scope())
    assert execution is not None
    checkpoint = service.create_checkpoint(
        execution.id, ["preflight"], ["execute"], {"position": 1}, scope()
    )
    service.execute(execution.id, scope())
    assert item.status is TaskStatus.QUEUED
    assert service.metrics.values["tiktok_scheduler_retry_total"] == 1
    item.status = TaskStatus.FAILED
    service.resume_checkpoint(checkpoint.id, scope())
    assert service.metrics.values["tiktok_scheduler_recovery_total"] == 1
    checkpoint.integrity = "tampered"
    with pytest.raises(ValueError):
        service.resume_checkpoint(checkpoint.id, scope())


def test_limits_backpressure_isolation_api_dashboard_statistics_and_integrations() -> (
    None
):
    limits = SchedulerLimits(
        maximum_global_tasks=2, maximum_workspace_tasks=1, maximum_queue_depth=1
    )
    service = TikTokAITaskScheduler(limits=limits)
    first = ready(service, task("one"))
    with pytest.raises(OverflowError):
        service.create_task(task("two"), scope())
    service.enqueue(first.id, scope())
    other = task("other", workspace="w2")
    service.create_task(other, scope("w2"))
    service.transition(other.id, TaskStatus.READY, scope("w2"))
    with pytest.raises(OverflowError):
        service.enqueue(other.id, scope("w2"))
    assert not any(
        platform in service.ports
        for platform in ("telegram", "whatsapp", "facebook", "instagram", "discord")
    )

    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    api_service = TikTokAITaskScheduler()
    register_task_scheduler_routes(app, api_service)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/task-scheduler/dashboard" in app.routes
    assert "/tiktok/task-scheduler/metrics" in app.routes
    dashboard = api_service.dashboard(
        SchedulerScope(
            "default", "default", "operator", frozenset({"tiktok:scheduler:admin"})
        )
    )
    assert dashboard["safety"]["captcha_bypass"] is False
    assert all(name in api_service.metrics.render_prometheus() for name in METRIC_NAMES)


def test_validation_rejects_invalid_intervals_limits_and_payload_sizes() -> None:
    with pytest.raises(ValueError):
        SchedulerLimits(maximum_retry_attempts=101).validate()
    with pytest.raises(ValueError):
        task(
            "interval",
            schedule=Schedule(ScheduleKind.INTERVAL, interval_seconds=0),
        ).validate(SchedulerLimits())
    with pytest.raises(ValueError):
        task("large", payload={"value": "x" * 100}).validate(
            replace(SchedulerLimits(), maximum_payload_size=20)
        )
