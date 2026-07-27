from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tiktok.data_collection import (
    METRICS,
    CollectionFilter,
    CollectionProject,
    CollectionSource,
    CollectionTask,
    DataScope,
    Dataset,
    JobKind,
    JobStatus,
    Pipeline,
    PipelineStage,
    ProjectStatus,
    StorageOperation,
    TikTokDataCollectionCenter,
)


@pytest.fixture
def scope() -> DataScope:
    return DataScope(
        "tenant-a",
        "workspace-a",
        "operator-a",
        frozenset({"tiktok:data:admin"}),
    )


@pytest.fixture
def center(scope: DataScope) -> TikTokDataCollectionCenter:
    value = TikTokDataCollectionCenter(concurrency_limit=2)
    value.add_source(
        CollectionSource(
            "source-1",
            scope.tenant,
            scope.workspace,
            "configured://account-videos",
            "account-1",
            {"resource": "owned-content"},
        ),
        scope,
    )
    value.create_dataset(
        Dataset(
            "dataset-1",
            scope.tenant,
            scope.workspace,
            "tiktok.video.v1",
            ["video_id", "created_at"],
            "kms://datasets/videos",
            {"video"},
        ),
        scope,
    )
    value.create_project(
        CollectionProject(
            "project-1",
            "Owned video analytics",
            "Collect configured owned-account analytics",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "source-1",
            "dataset-1",
        ),
        scope,
    )
    return value


def test_project_lifecycle_versioning_and_isolation(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    project = center.projects["project-1"]
    for status in (
        ProjectStatus.CONFIGURED,
        ProjectStatus.VALIDATED,
        ProjectStatus.QUEUED,
        ProjectStatus.RUNNING,
        ProjectStatus.COMPLETED,
        ProjectStatus.ARCHIVED,
    ):
        center.transition(project.id, status, scope)
    assert project.version == 7
    assert center.list_projects(DataScope("tenant-a", "other", "reader")) == []
    with pytest.raises(PermissionError):
        center.transition(
            project.id, ProjectStatus.DRAFT, DataScope("tenant-b", "other", "x")
        )
    with pytest.raises(ValueError, match="Invalid"):
        center.transition(project.id, ProjectStatus.RUNNING, scope)


def test_sources_datasets_filters_and_security_validation(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    assert center.sources["source-1"].health == "healthy"
    dataset = center.datasets["dataset-1"]
    assert dataset.version == 1 and dataset.retention_days == 90
    filters = CollectionFilter(
        ["launch"],
        (
            datetime(2026, 1, 1, tzinfo=timezone.utc),
            datetime(2026, 2, 1, tzinfo=timezone.utc),
        ),
        {"en"},
        {"US"},
        {"business"},
    )
    assert center.set_filter("project-1", filters, scope) is filters
    with pytest.raises(ValueError, match="date range"):
        CollectionFilter(
            date_range=(filters.date_range[1], filters.date_range[0])
        ).validate()
    with pytest.raises(ValueError, match="encrypted"):
        Dataset(
            "bad",
            scope.tenant,
            scope.workspace,
            "schema",
            ["id"],
            "file:///plain",
        ).validate()
    with pytest.raises(ValueError, match="secrets"):
        CollectionSource(
            "bad",
            scope.tenant,
            scope.workspace,
            "configured://bad",
            "account",
            {"token": "not-allowed"},
        ).validate()


def _validate_project(center: TikTokDataCollectionCenter, scope: DataScope) -> None:
    center.transition("project-1", ProjectStatus.CONFIGURED, scope)
    center.transition("project-1", ProjectStatus.VALIDATED, scope)


def test_manual_job_pipeline_history_analytics_dashboard_and_metrics(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    center.set_filter("project-1", CollectionFilter(["owned"]), scope)
    _validate_project(center, scope)
    pipeline = center.create_pipeline(
        Pipeline(
            "pipeline-1",
            scope.tenant,
            scope.workspace,
            "project-1",
        ),
        scope,
    )
    job = center.queue(
        CollectionTask(
            "job-1",
            "project-1",
            scope.tenant,
            scope.workspace,
            priority=90,
        ),
        scope,
    )
    assert center.process(scope) == [job]
    assert job.status is JobStatus.COMPLETED
    assert center.datasets["dataset-1"].record_count == 1
    assert pipeline.checkpoint.endswith("/analytics")
    assert center.history[0].operator == scope.actor
    assert [event["status"] for event in center.history[0].timeline] == [
        "running",
        "completed",
    ]
    analytics = center.analytics(scope)
    assert analytics["collection_volume"] == 1
    assert analytics["task_success"] == 1
    dashboard = center.dashboard(scope)
    assert set(dashboard["sections"]) == {
        "Projects",
        "Jobs",
        "Datasets",
        "Pipelines",
        "History",
        "Analytics",
        "Statistics",
    }
    assert set(center.metrics.snapshot()) == set(METRICS)
    assert "tiktok_collection_success_total 1.0" in (center.metrics.render_prometheus())


def test_scheduled_recurring_priority_retry_cancellation_and_failure(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    _validate_project(center, scope)
    recurring = CollectionTask(
        "job-recurring",
        "project-1",
        scope.tenant,
        scope.workspace,
        JobKind.RECURRING,
        80,
        1,
        2,
        "0 * * * *",
    )
    center.queue(recurring, scope)
    assert center.cancel(recurring.id, scope).status is JobStatus.CANCELLED
    with pytest.raises(ValueError, match="schedule"):
        CollectionTask(
            "bad",
            "project-1",
            scope.tenant,
            scope.workspace,
            JobKind.SCHEDULED,
        ).validate()

    center.projects["project-1"].status = ProjectStatus.VALIDATED
    center.sources["source-1"].health = "degraded"
    failed = center.queue(
        CollectionTask(
            "job-failed",
            "project-1",
            scope.tenant,
            scope.workspace,
        ),
        scope,
    )
    center.process(scope)
    assert failed.status is JobStatus.FAILED
    assert failed.attempts == 1
    assert failed.failure_reason == "RuntimeError"
    assert center.analytics(scope)["task_failure"] == 1


def test_storage_archive_restore_import_export(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    for operation in ("import", "export", "archive", "restore"):
        center.storage_operation(
            StorageOperation(
                f"storage-{operation}",
                "dataset-1",
                scope.tenant,
                scope.workspace,
                operation,
                f"vault://datasets/{operation}",
            ),
            scope,
        )
    assert not center.datasets["dataset-1"].archived
    assert len(center.storage_history) == 4
    with pytest.raises(ValueError, match="Unsupported"):
        StorageOperation(
            "bad",
            "dataset-1",
            scope.tenant,
            scope.workspace,
            "delete",
            "kms://datasets/bad",
        ).validate()


def test_api_dashboard_routes_and_mock_only_runtime(
    center: TikTokDataCollectionCenter,
) -> None:
    from tiktok.data_collection.api import (
        ROUTES,
        register_data_collection_routes,
    )

    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str], object, list[str]]] = []

        def add_api_route(
            self,
            path: str,
            endpoint: object,
            methods: list[str],
            tags: list[str],
        ) -> None:
            self.routes.append((path, methods, endpoint, tags))

    app = App()
    register_data_collection_routes(app, center)
    paths = {route[0] for route in app.routes}
    assert set(ROUTES) <= paths
    assert {"/tiktok/data/dashboard", "/tiktok/data/metrics"} <= paths


def test_pipeline_order_rbac_audit_and_no_other_social_modules(
    center: TikTokDataCollectionCenter, scope: DataScope
) -> None:
    with pytest.raises(ValueError, match="stage order"):
        Pipeline(
            "bad",
            scope.tenant,
            scope.workspace,
            "project-1",
            [PipelineStage.STORAGE, PipelineStage.COLLECTION],
        ).validate()
    with pytest.raises(PermissionError, match="RBAC"):
        center.create_dataset(
            Dataset(
                "forbidden",
                scope.tenant,
                scope.workspace,
                "schema",
                ["id"],
                "kms://dataset/forbidden",
            ),
            DataScope(scope.tenant, scope.workspace, "reader"),
        )
    assert center.audit
    assert not any(
        name in action["action"]
        for action in center.audit
        for name in ("telegram", "whatsapp", "facebook", "instagram", "discord")
    )
