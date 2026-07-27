from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.publishing_center import (
    ApprovalState,
    FailureCategory,
    PublishingJob,
    PublishingSchedule,
    PublishingScope,
    PublishingStatus,
    RetryPolicy,
    ScheduleMode,
    TikTokPublishingCenter,
)
from tiktok.publishing_center.api import ROUTES, register_publishing_center_routes

PERMISSIONS = frozenset({"tiktok:publishing:admin"})


def scope(workspace: str = "workspace-a") -> PublishingScope:
    return PublishingScope("tenant-a", workspace, "operator", PERMISSIONS)


def job(
    reference: str = "job-1",
    *,
    priority: int = 50,
    schedule: PublishingSchedule | None = None,
) -> PublishingJob:
    return PublishingJob(
        reference,
        f"Publish {reference}",
        "project-1",
        "account-1",
        "media-1",
        "tenant-a",
        "workspace-a",
        "browser-runtime",
        priority=priority,
        schedule=schedule or PublishingSchedule(),
    )


def approved(center: TikTokPublishingCenter, value: PublishingJob) -> PublishingJob:
    center.create_job(value, scope())
    center.review(value.id, scope(), approve=True, notes="Ready")
    return center.enqueue(value.id, scope())


def test_job_approval_queue_execution_history_analytics_and_metrics() -> None:
    center = TikTokPublishingCenter()
    value = approved(center, job())
    assert value.status is PublishingStatus.QUEUED
    [completed] = center.tick(scope())
    assert completed.status is PublishingStatus.PUBLISHED
    assert center.approvals[value.id].state is ApprovalState.APPROVED
    assert center.analytics(scope())["success_rate"] == 1.0
    assert center.metrics.snapshot()["tiktok_publish_success_total"] == 1
    assert {entry.event for entry in center.history} >= {
        "job.created",
        "job.approved",
        "job.queued",
        "job.publishing",
        "job.published",
    }
    assert center.notifications[-1]["type"] == "queue_complete"


def test_priority_fifo_workspace_account_retry_and_delayed_queues() -> None:
    center = TikTokPublishingCenter()
    low = approved(center, job("low", priority=1))
    high = approved(center, job("high", priority=100))
    assert center.queue(scope())[0] is high
    assert center.queue(scope(), kind="fifo")[0] is low
    assert center.queue(scope(), kind="workspace")
    assert center.queue(scope(), kind="account")
    high.attempts = 1
    high.next_attempt_at = datetime.now(timezone.utc) + timedelta(minutes=1)
    assert center.queue(scope(), kind="retry") == [high]
    assert center.queue(scope(), kind="delayed") == [high]


def test_scheduler_calendar_and_concurrency_limit() -> None:
    run_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    schedule = PublishingSchedule(mode=ScheduleMode.SCHEDULED, run_at=run_at)
    center = TikTokPublishingCenter(concurrency_limit=1)
    first = approved(center, job("scheduled-1", schedule=schedule))
    approved(center, job("scheduled-2", schedule=schedule))
    assert first.status is PublishingStatus.SCHEDULED
    assert len(center.dashboard(scope())["calendar"]) == 2
    assert len(center.tick(scope())) == 1


def test_approval_reject_expire_reapprove_and_enforcement() -> None:
    center = TikTokPublishingCenter()
    value = center.create_job(job(), scope())
    center.review(value.id, scope(), approve=False, notes="Needs changes")
    with pytest.raises(PermissionError):
        center.enqueue(value.id, scope())
    approval = center.review(
        value.id,
        scope(),
        approve=True,
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
    )
    assert center.expire_approvals(scope()) == 1
    assert approval.state is ApprovalState.EXPIRED
    center.review(value.id, scope(), approve=True, notes="Reapproved")
    assert approval.state is ApprovalState.APPROVED


class FailingPublisher:
    def publish(self, value: PublishingJob) -> bool:
        return False


def test_failure_retry_backoff_manual_recovery_and_notifications() -> None:
    center = TikTokPublishingCenter(publisher=FailingPublisher())
    value = job()
    value.retry_policy = RetryPolicy(retry_delay_seconds=10)
    approved(center, value)
    center.tick(scope())
    assert value.status is PublishingStatus.QUEUED
    assert value.next_attempt_at is not None
    assert center.failures[0].category is FailureCategory.BROWSER
    assert center.metrics.snapshot()["tiktok_publish_retry_total"] == 1
    center.recover(value.id, scope())
    assert center.failures[0].recovered_by == "operator"


def test_security_isolation_rbac_and_no_secrets() -> None:
    center = TikTokPublishingCenter()
    with pytest.raises(ValueError, match="secrets"):
        center.create_job(
            PublishingJob(
                "bad",
                "Bad",
                "project",
                "account",
                "media",
                "tenant-a",
                "workspace-a",
                "publisher",
                metadata={"token": "redacted"},
            ),
            scope(),
        )
    center.create_job(job(), scope())
    assert center.list_jobs(scope("workspace-b")) == []
    with pytest.raises(PermissionError):
        center.cancel("job-1", scope("workspace-b"))
    with pytest.raises(PermissionError):
        center.list_jobs(
            PublishingScope("tenant-a", "workspace-a", "viewer", frozenset())
        )


class App:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, list[str], list[str]]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, endpoint, methods, tags))


def test_api_dashboard_metrics_and_route_inventory() -> None:
    app = App()
    center = TikTokPublishingCenter()
    register_publishing_center_routes(app, center)
    paths = {path for path, *_ in app.routes}
    assert set(ROUTES) <= paths
    assert "/tiktok/publishing/dashboard" in paths
    assert "/tiktok/publishing/metrics" in paths
    assert set(center.dashboard(scope())) >= {
        "queue",
        "calendar",
        "schedules",
        "approvals",
        "failures",
        "retries",
        "history",
        "analytics",
        "statistics",
    }
    assert "tiktok_publish_jobs_total" in center.metrics.render_prometheus()


def test_models_validate_timezone_window_retry_and_priority() -> None:
    with pytest.raises(ValueError):
        job(priority=101).validate()
    with pytest.raises(ValueError):
        PublishingSchedule(timezone="Not/AZone").validate()
    with pytest.raises(ValueError):
        PublishingSchedule(mode=ScheduleMode.RECURRING).validate()
    with pytest.raises(ValueError):
        RetryPolicy(maximum_attempts=0).validate()
