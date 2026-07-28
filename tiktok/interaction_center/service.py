"""Tenant-isolated Interaction Center orchestration and approval enforcement."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .adapters import ExecutionPort, NullExecutionPort, NullReferencePort, ReferencePort
from .metrics import InteractionMetrics
from .models import (
    ApprovalStatus,
    DraftVersion,
    InteractionDraft,
    InteractionProject,
    InteractionScope,
    InteractionTask,
    InteractionTemplate,
    Lifecycle,
    Notification,
    QueueKind,
    ReviewRecord,
    ReviewStatus,
    utcnow,
)


class TikTokInteractionCenter:
    """Safe control plane: reviewed work only, with no bulk or bypass features."""

    def __init__(
        self,
        *,
        accounts: ReferencePort | None = None,
        browsers: ExecutionPort | None = None,
        proxies: ReferencePort | None = None,
        content: ReferencePort | None = None,
        publishing: ExecutionPort | None = None,
        collection: ReferencePort | None = None,
        concurrency_limit: int = 5,
    ) -> None:
        if not 1 <= concurrency_limit <= 100:
            raise ValueError("Concurrency limit must be within [1, 100].")
        self.accounts = accounts or NullReferencePort()
        self.browsers = browsers or NullExecutionPort()
        self.proxies = proxies or NullReferencePort()
        self.content = content or NullReferencePort()
        self.publishing = publishing or NullExecutionPort()
        self.collection = collection or NullReferencePort()
        self.concurrency_limit = concurrency_limit
        self.projects: dict[str, InteractionProject] = {}
        self.tasks: dict[str, InteractionTask] = {}
        self.drafts: dict[str, InteractionDraft] = {}
        self.templates: dict[str, InteractionTemplate] = {}
        self.reviews: dict[str, ReviewRecord] = {}
        self.notifications: list[Notification] = []
        self.history: list[dict[str, Any]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = InteractionMetrics()

    @staticmethod
    def _require(scope: InteractionScope, action: str) -> None:
        permission = f"tiktok:interaction:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:interaction:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: InteractionScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _audit(self, action: str, resource: str, scope: InteractionScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": utcnow().isoformat(),
            }
        )

    def _notify(self, kind: str, resource: str, scope: InteractionScope) -> None:
        self.notifications.append(
            Notification(
                kind, resource, scope.tenant, scope.workspace, kind.replace("_", " ")
            )
        )

    def create_project(
        self, project: InteractionProject, scope: InteractionScope
    ) -> InteractionProject:
        self._require(scope, "write")
        self._scoped(project, scope)
        project.validate()
        if project.id in self.projects:
            raise ValueError("Project ID must be unique.")
        self.projects[project.id] = project
        self.metrics.increment("tiktok_interaction_projects_total")
        self._audit("project.create", project.id, scope)
        return project

    def list_projects(self, scope: InteractionScope) -> list[InteractionProject]:
        self._require(scope, "read")
        return [
            p
            for p in self.projects.values()
            if p.tenant == scope.tenant
            and p.workspace == scope.workspace
            and p.status is not Lifecycle.DELETED
        ]

    def transition_project(
        self,
        reference: str,
        status: Lifecycle,
        scope: InteractionScope,
    ) -> InteractionProject:
        self._require(scope, "write")
        project = self.projects[reference]
        self._scoped(project, scope)
        transitions = {
            Lifecycle.DRAFT: {Lifecycle.REVIEW, Lifecycle.ARCHIVED, Lifecycle.DELETED},
            Lifecycle.REVIEW: {Lifecycle.DRAFT, Lifecycle.APPROVED},
            Lifecycle.APPROVED: {
                Lifecycle.DRAFT,
                Lifecycle.QUEUED,
                Lifecycle.SCHEDULED,
            },
            Lifecycle.QUEUED: {Lifecycle.RUNNING, Lifecycle.FAILED},
            Lifecycle.SCHEDULED: {Lifecycle.QUEUED, Lifecycle.RUNNING},
            Lifecycle.RUNNING: {Lifecycle.COMPLETED, Lifecycle.FAILED},
            Lifecycle.COMPLETED: {Lifecycle.ARCHIVED},
            Lifecycle.FAILED: {Lifecycle.QUEUED, Lifecycle.ARCHIVED},
            Lifecycle.ARCHIVED: {Lifecycle.DRAFT, Lifecycle.DELETED},
            Lifecycle.DELETED: set(),
        }
        if status not in transitions[project.status]:
            raise ValueError(
                f"Invalid interaction transition: "
                f"{project.status.value} -> {status.value}"
            )
        project.status = status
        project.version += 1
        project.updated_at = utcnow()
        self._audit(f"project.{status.value}", project.id, scope)
        return project

    def create_template(
        self, template: InteractionTemplate, scope: InteractionScope
    ) -> InteractionTemplate:
        self._require(scope, "write")
        self._scoped(template, scope)
        template.validate()
        if template.id in self.templates:
            raise ValueError("Template ID must be unique.")
        self.templates[template.id] = template
        self._audit("template.create", template.id, scope)
        return template

    def export_template(
        self, reference: str, scope: InteractionScope
    ) -> dict[str, Any]:
        template = self.templates[reference]
        self._scoped(template, scope)
        return asdict(template)

    def clone_template(
        self, reference: str, new_id: str, scope: InteractionScope
    ) -> InteractionTemplate:
        source = self.templates[reference]
        self._scoped(source, scope)
        clone = deepcopy(source)
        clone.id, clone.name, clone.version = new_id, f"{source.name} (copy)", 1
        return self.create_template(clone, scope)

    def import_template(
        self, payload: dict[str, Any], scope: InteractionScope
    ) -> InteractionTemplate:
        template = InteractionTemplate(**payload)
        template.imported = True
        return self.create_template(template, scope)

    def create_draft(
        self, draft: InteractionDraft, scope: InteractionScope
    ) -> InteractionDraft:
        self._require(scope, "write")
        self._scoped(draft, scope)
        self._scoped(self.projects[draft.project_reference], scope)
        draft.validate()
        if draft.id in self.drafts:
            raise ValueError("Draft ID must be unique.")
        if draft.template_reference:
            self._scoped(self.templates[draft.template_reference], scope)
        draft.history.append(
            DraftVersion(1, draft.content, deepcopy(draft.variables), scope.actor)
        )
        self.drafts[draft.id] = draft
        self._audit("draft.create", draft.id, scope)
        return draft

    def edit_draft(
        self,
        reference: str,
        content: str,
        variables: dict[str, str],
        scope: InteractionScope,
    ) -> InteractionDraft:
        self._require(scope, "write")
        draft = self.drafts[reference]
        self._scoped(draft, scope)
        if not content.strip():
            raise ValueError("Draft content is required.")
        draft.content, draft.variables = content, deepcopy(variables)
        draft.version += 1
        draft.review_status, draft.approval_status = (
            ReviewStatus.NOT_REQUESTED,
            ApprovalStatus.PENDING,
        )
        draft.history.append(
            DraftVersion(draft.version, content, deepcopy(variables), scope.actor)
        )
        self._audit("draft.edit", draft.id, scope)
        return draft

    def submit_review(
        self, review: ReviewRecord, scope: InteractionScope
    ) -> ReviewRecord:
        self._require(scope, "write")
        self._scoped(review, scope)
        draft = self.drafts[review.draft_reference]
        self._scoped(draft, scope)
        if review.id in self.reviews:
            raise ValueError("Review ID must be unique.")
        draft.review_status = ReviewStatus.PENDING
        self.reviews[review.id] = review
        self._notify("review_required", review.id, scope)
        self._audit("review.submit", review.id, scope)
        return review

    def decide_review(
        self, reference: str, approve: bool, notes: str, scope: InteractionScope
    ) -> ReviewRecord:
        self._require(scope, "approve")
        review = self.reviews[reference]
        self._scoped(review, scope)
        if review.expires_at and review.expires_at <= utcnow():
            review.status, review.approval_status = (
                ReviewStatus.EXPIRED,
                ApprovalStatus.EXPIRED,
            )
            raise ValueError("Review has expired.")
        review.reviewer, review.notes, review.updated_at = scope.actor, notes, utcnow()
        review.status = ReviewStatus.APPROVED if approve else ReviewStatus.REJECTED
        review.approval_status = (
            ApprovalStatus.APPROVED if approve else ApprovalStatus.REJECTED
        )
        draft = self.drafts[review.draft_reference]
        draft.review_status, draft.approval_status = (
            review.status,
            review.approval_status,
        )
        self._audit("review.approve" if approve else "review.reject", review.id, scope)
        return review

    def reapprove(
        self, reference: str, notes: str, scope: InteractionScope
    ) -> ReviewRecord:
        return self.decide_review(reference, True, notes, scope)

    def create_task(
        self, task: InteractionTask, scope: InteractionScope
    ) -> InteractionTask:
        self._require(scope, "write")
        self._scoped(task, scope)
        self._scoped(self.projects[task.project_reference], scope)
        self._scoped(self.drafts[task.draft_reference], scope)
        task.validate()
        if task.id in self.tasks:
            raise ValueError("Task ID must be unique.")
        self.tasks[task.id] = task
        self.metrics.increment("tiktok_interaction_tasks_total")
        self._audit("task.create", task.id, scope)
        return task

    def retry_task(self, reference: str, scope: InteractionScope) -> InteractionTask:
        self._require(scope, "queue")
        task = self.tasks[reference]
        self._scoped(task, scope)
        if task.status is not Lifecycle.FAILED:
            raise ValueError("Only failed tasks can be retried.")
        if task.attempts > task.maximum_retries:
            raise ValueError("Task retry limit has been exhausted.")
        task.status = Lifecycle.QUEUED
        task.queue = QueueKind.RETRY
        task.queued_at = utcnow()
        self.metrics.increment("tiktok_interaction_queue_total")
        self._audit("task.retry", task.id, scope)
        return task

    def queue_task(
        self,
        reference: str,
        scope: InteractionScope,
        *,
        scheduled_for: datetime | None = None,
    ) -> InteractionTask:
        self._require(scope, "queue")
        task = self.tasks[reference]
        self._scoped(task, scope)
        draft = self.drafts[task.draft_reference]
        if draft.approval_status is not ApprovalStatus.APPROVED:
            self._notify("approval_required", draft.id, scope)
            raise PermissionError("Approved review is required before queueing.")
        task.scheduled_for = scheduled_for
        task.status = Lifecycle.SCHEDULED if scheduled_for else Lifecycle.QUEUED
        task.queue = QueueKind.DELAYED if scheduled_for else QueueKind.PRIORITY
        task.queued_at = utcnow()
        self.metrics.increment("tiktok_interaction_queue_total")
        self._audit("task.queue", task.id, scope)
        return task

    def run_next(self, scope: InteractionScope) -> InteractionTask | None:
        self._require(scope, "execute")
        running = sum(
            1
            for task in self.tasks.values()
            if task.tenant == scope.tenant
            and task.workspace == scope.workspace
            and task.status is Lifecycle.RUNNING
        )
        if running >= self.concurrency_limit:
            return None
        ready = [
            task
            for task in self.tasks.values()
            if task.tenant == scope.tenant
            and task.workspace == scope.workspace
            and task.status in {Lifecycle.QUEUED, Lifecycle.SCHEDULED}
            and (task.scheduled_for is None or task.scheduled_for <= utcnow())
        ]
        if not ready:
            return None
        task = max(ready, key=lambda value: value.priority)
        task.status, task.started_at = Lifecycle.RUNNING, utcnow()
        ok = self.browsers.execute(
            task.id, task.draft_reference, scope.tenant, scope.workspace
        )
        task.finished_at = utcnow()
        task.status = Lifecycle.COMPLETED if ok else Lifecycle.FAILED
        if ok:
            self.metrics.increment("tiktok_interaction_completed_total")
            self._notify("completed", task.id, scope)
        else:
            task.attempts += 1
            task.failure_reason = "Bounded runtime execution failed."
            self.metrics.increment("tiktok_interaction_failed_total")
            self._notify(
                "retry_required" if task.attempts <= task.maximum_retries else "failed",
                task.id,
                scope,
            )
            if task.attempts <= task.maximum_retries:
                task.queue = QueueKind.RETRY
        latency = (task.finished_at - task.started_at).total_seconds()
        self.metrics.set("tiktok_interaction_latency_seconds", latency)
        self.history.append(
            {
                "task": task.id,
                "status": task.status.value,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "finished_at": task.finished_at.isoformat(),
            }
        )
        self._audit(f"task.{task.status.value}", task.id, scope)
        return task

    def analytics(self, scope: InteractionScope) -> dict[str, Any]:
        self._require(scope, "read")
        tasks = [
            t
            for t in self.tasks.values()
            if t.tenant == scope.tenant and t.workspace == scope.workspace
        ]
        completed = sum(t.status is Lifecycle.COMPLETED for t in tasks)
        failed = sum(t.status is Lifecycle.FAILED for t in tasks)
        queue_times = [
            (t.started_at - t.queued_at).total_seconds()
            for t in tasks
            if t.started_at and t.queued_at
        ]
        execution_times = [
            (t.finished_at - t.started_at).total_seconds()
            for t in tasks
            if t.finished_at and t.started_at
        ]
        total = len(tasks)
        return {
            "task_volume": total,
            "completion_rate": completed / total if total else 0.0,
            "failure_rate": failed / total if total else 0.0,
            "queue_time": sum(queue_times) / len(queue_times) if queue_times else 0.0,
            "execution_time": sum(execution_times) / len(execution_times)
            if execution_times
            else 0.0,
            "trend": [
                {"status": key, "count": sum(t.status.value == key for t in tasks)}
                for key in ("completed", "failed")
            ],
        }

    def dashboard(self, scope: InteractionScope) -> dict[str, Any]:
        self._require(scope, "read")

        def scoped(values: Any) -> list[Any]:
            return [
                value
                for value in values
                if value.tenant == scope.tenant and value.workspace == scope.workspace
            ]

        return {
            "projects": len(self.list_projects(scope)),
            "tasks": len(scoped(self.tasks.values())),
            "drafts": len(scoped(self.drafts.values())),
            "templates": len(scoped(self.templates.values())),
            "reviews": len(scoped(self.reviews.values())),
            "queues": {
                kind.value: sum(
                    t.queue is kind
                    and t.status
                    in {Lifecycle.QUEUED, Lifecycle.SCHEDULED, Lifecycle.FAILED}
                    for t in scoped(self.tasks.values())
                )
                for kind in QueueKind
            },
            "analytics": self.analytics(scope),
            "history": [
                item
                for item in self.history
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ],
            "statistics": self.metrics.snapshot(),
            "notifications": [asdict(n) for n in scoped(self.notifications)],
        }
