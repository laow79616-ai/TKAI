"""Tenant-isolated orchestration for enterprise TikTok data collection."""

from __future__ import annotations

from datetime import datetime, timezone
from time import monotonic
from typing import Any

from .adapters import (
    AccountCenterPort,
    AutomationPort,
    BrowserRuntimePort,
    NullAccountCenterPort,
    NullAutomationPort,
    NullBrowserRuntimePort,
    NullProxyCenterPort,
    NullWorkflowPort,
    ProxyCenterPort,
    WorkflowPort,
)
from .metrics import CollectionMetrics
from .models import (
    CollectionFilter,
    CollectionProject,
    CollectionSource,
    CollectionTask,
    DataScope,
    Dataset,
    ExecutionRecord,
    JobKind,
    JobStatus,
    Pipeline,
    ProjectStatus,
    StorageOperation,
    utcnow,
)


class TikTokDataCollectionCenter:
    """Collection control plane; all external activity stays behind bounded ports."""

    def __init__(
        self,
        *,
        accounts: AccountCenterPort | None = None,
        browsers: BrowserRuntimePort | None = None,
        proxies: ProxyCenterPort | None = None,
        workflows: WorkflowPort | None = None,
        automation: AutomationPort | None = None,
        concurrency_limit: int = 10,
    ) -> None:
        if not 1 <= concurrency_limit <= 100:
            raise ValueError("Concurrency limit must be within [1, 100].")
        self.accounts = accounts or NullAccountCenterPort()
        self.browsers = browsers or NullBrowserRuntimePort()
        self.proxies = proxies or NullProxyCenterPort()
        self.workflows = workflows or NullWorkflowPort()
        self.automation = automation or NullAutomationPort()
        self.concurrency_limit = concurrency_limit
        self.sources: dict[str, CollectionSource] = {}
        self.datasets: dict[str, Dataset] = {}
        self.filters: dict[str, CollectionFilter] = {}
        self.projects: dict[str, CollectionProject] = {}
        self.jobs: dict[str, CollectionTask] = {}
        self.pipelines: dict[str, Pipeline] = {}
        self.history: list[ExecutionRecord] = []
        self.storage_history: list[StorageOperation] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = CollectionMetrics()

    @staticmethod
    def _require(scope: DataScope, action: str) -> None:
        permission = f"tiktok:data:{action}"
        if permission not in scope.permissions and "tiktok:data:admin" not in (
            scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: DataScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _audit(self, action: str, resource: str, scope: DataScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "operator": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def add_source(
        self, source: CollectionSource, scope: DataScope
    ) -> CollectionSource:
        self._require(scope, "write")
        self._scoped(source, scope)
        source.validate()
        if not self.accounts.validate(
            source.account_reference, scope.tenant, scope.workspace
        ):
            raise ValueError("Account Center rejected the account reference.")
        if source.id in self.sources:
            raise ValueError("Source ID must be unique.")
        source.validation = "valid"
        source.health = (
            "healthy"
            if self.proxies.healthy_for(
                source.account_reference, scope.tenant, scope.workspace
            )
            else "degraded"
        )
        self.sources[source.id] = source
        self._audit("source.create", source.id, scope)
        return source

    def create_dataset(self, dataset: Dataset, scope: DataScope) -> Dataset:
        self._require(scope, "write")
        self._scoped(dataset, scope)
        dataset.validate()
        if dataset.id in self.datasets:
            raise ValueError("Dataset ID must be unique.")
        self.datasets[dataset.id] = dataset
        self.metrics.increment("tiktok_dataset_total")
        self._audit("dataset.create", dataset.id, scope)
        return dataset

    def create_project(
        self, project: CollectionProject, scope: DataScope
    ) -> CollectionProject:
        self._require(scope, "write")
        self._scoped(project, scope)
        project.validate()
        self._scoped(self.sources[project.source_reference], scope)
        self._scoped(self.datasets[project.dataset_reference], scope)
        if project.id in self.projects:
            raise ValueError("Project ID must be unique.")
        self.projects[project.id] = project
        self.metrics.increment("tiktok_collection_projects_total")
        self._audit("project.create", project.id, scope)
        return project

    def list_projects(self, scope: DataScope) -> list[CollectionProject]:
        self._require(scope, "read")
        return [
            project
            for project in self.projects.values()
            if project.tenant == scope.tenant
            and project.workspace == scope.workspace
            and project.status is not ProjectStatus.DELETED
        ]

    def set_filter(
        self, project_reference: str, filters: CollectionFilter, scope: DataScope
    ) -> CollectionFilter:
        self._require(scope, "write")
        project = self.projects[project_reference]
        self._scoped(project, scope)
        filters.validate()
        self.filters[project_reference] = filters
        self._audit("filter.configure", project_reference, scope)
        return filters

    def transition(
        self, project_reference: str, status: ProjectStatus, scope: DataScope
    ) -> CollectionProject:
        self._require(scope, "write")
        project = self.projects[project_reference]
        self._scoped(project, scope)
        transitions = {
            ProjectStatus.DRAFT: {
                ProjectStatus.CONFIGURED,
                ProjectStatus.ARCHIVED,
                ProjectStatus.DELETED,
            },
            ProjectStatus.CONFIGURED: {
                ProjectStatus.DRAFT,
                ProjectStatus.VALIDATED,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.VALIDATED: {
                ProjectStatus.CONFIGURED,
                ProjectStatus.QUEUED,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.QUEUED: {
                ProjectStatus.RUNNING,
                ProjectStatus.PAUSED,
                ProjectStatus.FAILED,
            },
            ProjectStatus.RUNNING: {
                ProjectStatus.PAUSED,
                ProjectStatus.COMPLETED,
                ProjectStatus.FAILED,
            },
            ProjectStatus.PAUSED: {
                ProjectStatus.QUEUED,
                ProjectStatus.RUNNING,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.COMPLETED: {ProjectStatus.ARCHIVED},
            ProjectStatus.FAILED: {
                ProjectStatus.QUEUED,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.ARCHIVED: {
                ProjectStatus.DRAFT,
                ProjectStatus.DELETED,
            },
            ProjectStatus.DELETED: set(),
        }
        if status not in transitions[project.status]:
            raise ValueError(
                f"Invalid collection transition: {project.status.value}"
                f" -> {status.value}"
            )
        project.status = status
        project.version += 1
        project.updated_at = utcnow()
        self._audit(f"project.{status.value}", project.id, scope)
        return project

    def create_pipeline(self, pipeline: Pipeline, scope: DataScope) -> Pipeline:
        self._require(scope, "write")
        self._scoped(pipeline, scope)
        self._scoped(self.projects[pipeline.project_reference], scope)
        pipeline.validate()
        self.pipelines[pipeline.id] = pipeline
        self._audit("pipeline.create", pipeline.id, scope)
        return pipeline

    def queue(self, task: CollectionTask, scope: DataScope) -> CollectionTask:
        self._require(scope, "execute")
        self._scoped(task, scope)
        task.validate()
        project = self.projects[task.project_reference]
        self._scoped(project, scope)
        if project.status is not ProjectStatus.VALIDATED:
            raise ValueError("Only validated projects can be queued.")
        if task.id in self.jobs:
            raise ValueError("Job ID must be unique.")
        if task.kind is not JobKind.MANUAL and not self.automation.schedule(
            task.id, task.schedule, f"{scope.tenant}/{scope.workspace}"
        ):
            raise RuntimeError("Automation rejected the schedule.")
        self.jobs[task.id] = task
        self.transition(project.id, ProjectStatus.QUEUED, scope)
        self.metrics.increment("tiktok_collection_jobs_total")
        self._audit("job.queue", task.id, scope)
        return task

    def cancel(self, reference: str, scope: DataScope) -> CollectionTask:
        self._require(scope, "execute")
        task = self.jobs[reference]
        self._scoped(task, scope)
        if not task.cancellable or task.status in {
            JobStatus.COMPLETED,
            JobStatus.FAILED,
            JobStatus.CANCELLED,
        }:
            raise ValueError("Job cannot be cancelled.")
        task.status = JobStatus.CANCELLED
        task.finished_at = utcnow()
        self._audit("job.cancel", task.id, scope)
        return task

    def process(self, scope: DataScope) -> list[CollectionTask]:
        self._require(scope, "execute")
        pending = sorted(
            (
                task
                for task in self.jobs.values()
                if task.tenant == scope.tenant
                and task.workspace == scope.workspace
                and task.status is JobStatus.QUEUED
            ),
            key=lambda task: (-task.priority, task.created_at),
        )[: self.concurrency_limit]
        for task in pending:
            self._run(task, scope)
        return pending

    def _run(self, task: CollectionTask, scope: DataScope) -> None:
        project = self.projects[task.project_reference]
        source = self.sources[project.source_reference]
        dataset = self.datasets[project.dataset_reference]
        pipeline = next(
            (
                item
                for item in self.pipelines.values()
                if item.project_reference == project.id
            ),
            None,
        )
        started = monotonic()
        task.status = JobStatus.RUNNING
        task.started_at = utcnow()
        project.status = ProjectStatus.RUNNING
        timeline = [{"status": "running", "at": task.started_at.isoformat()}]
        try:
            if source.health != "healthy":
                raise RuntimeError("Configured source is not healthy.")
            records = self.browsers.collect(
                source,
                self.filters.get(project.id, CollectionFilter()),
                scope.tenant,
                scope.workspace,
            )
            if pipeline:
                for stage in pipeline.stages:
                    pipeline.checkpoint = self.workflows.checkpoint(
                        pipeline.id,
                        stage.value,
                        f"{scope.tenant}/{scope.workspace}",
                    )
            dataset.record_count += len(records)
            dataset.version += 1
            task.status = JobStatus.COMPLETED
            project.status = ProjectStatus.COMPLETED
            self.metrics.increment("tiktok_collection_success_total")
        except Exception as error:
            task.status = JobStatus.FAILED
            task.attempts += 1
            task.failure_reason = type(error).__name__
            project.status = ProjectStatus.FAILED
            self.metrics.increment("tiktok_collection_failure_total")
        finally:
            task.finished_at = utcnow()
            project.version += 1
            project.updated_at = utcnow()
            timeline.append(
                {"status": task.status.value, "at": task.finished_at.isoformat()}
            )
            self.metrics.set("tiktok_collection_latency_seconds", monotonic() - started)
            self.history.append(
                ExecutionRecord(
                    task.id,
                    project.id,
                    scope.tenant,
                    scope.workspace,
                    task.status,
                    scope.actor,
                    project.version,
                    timeline,
                    f"audit://collection/{task.id}",
                    task.started_at,
                    task.finished_at,
                )
            )
            self._audit(f"job.{task.status.value}", task.id, scope)

    def storage_operation(
        self, operation: StorageOperation, scope: DataScope
    ) -> StorageOperation:
        self._require(scope, "storage")
        self._scoped(operation, scope)
        dataset = self.datasets[operation.dataset_reference]
        self._scoped(dataset, scope)
        operation.validate()
        dataset.archived = operation.operation == "archive"
        if operation.operation == "restore":
            dataset.archived = False
        self.storage_history.append(operation)
        self._audit(f"storage.{operation.operation}", operation.id, scope)
        return operation

    def analytics(self, scope: DataScope) -> dict[str, Any]:
        self._require(scope, "read")
        projects = self.list_projects(scope)
        jobs = [
            task
            for task in self.jobs.values()
            if task.tenant == scope.tenant and task.workspace == scope.workspace
        ]
        datasets = [
            dataset
            for dataset in self.datasets.values()
            if dataset.tenant == scope.tenant and dataset.workspace == scope.workspace
        ]
        completed = sum(task.status is JobStatus.COMPLETED for task in jobs)
        failed = sum(task.status is JobStatus.FAILED for task in jobs)
        return {
            "collection_volume": sum(dataset.record_count for dataset in datasets),
            "task_success": completed,
            "task_failure": failed,
            "dataset_growth": {
                dataset.id: dataset.record_count for dataset in datasets
            },
            "pipeline_runtime": self.metrics.snapshot()[
                "tiktok_collection_latency_seconds"
            ],
            "projects": len(projects),
        }

    def dashboard(self, scope: DataScope) -> dict[str, Any]:
        analytics = self.analytics(scope)
        return {
            "sections": [
                "Projects",
                "Jobs",
                "Datasets",
                "Pipelines",
                "History",
                "Analytics",
                "Statistics",
            ],
            "projects": analytics["projects"],
            "jobs": sum(
                task.tenant == scope.tenant and task.workspace == scope.workspace
                for task in self.jobs.values()
            ),
            "datasets": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self.datasets.values()
            ),
            "pipelines": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self.pipelines.values()
            ),
            "history": sum(
                item.tenant == scope.tenant and item.workspace == scope.workspace
                for item in self.history
            ),
            "analytics": analytics,
            "statistics": self.metrics.snapshot(),
        }
