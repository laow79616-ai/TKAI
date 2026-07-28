"""Enterprise TikTok content lifecycle, library, scheduling and publishing."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
from time import monotonic
from typing import Any

from .adapters import (
    AccountCenterPort,
    BrowserRuntimePort,
    FarmingPort,
    NullAccountCenterPort,
    NullBrowserRuntimePort,
    NullFarmingPort,
    NullProxyCenterPort,
    ProxyCenterPort,
)
from .metrics import ContentMetrics
from .models import (
    ApprovalStatus,
    Caption,
    ContentDraft,
    ContentProject,
    ContentScope,
    ContentTemplate,
    Cover,
    DraftVersion,
    HashtagSet,
    MediaAsset,
    ProjectStatus,
    PublishingSchedule,
    PublishJob,
    QueueStatus,
    ReviewStatus,
    utcnow,
)


class TikTokContentCenter:
    """A tenant-isolated control plane; storage and browser work stay delegated."""

    def __init__(
        self,
        *,
        accounts: AccountCenterPort | None = None,
        browsers: BrowserRuntimePort | None = None,
        proxies: ProxyCenterPort | None = None,
        farming: FarmingPort | None = None,
        concurrency_limit: int = 5,
        approval_required: bool = True,
    ) -> None:
        if not 1 <= concurrency_limit <= 100:
            raise ValueError("Concurrency limit must be within [1, 100].")
        self.accounts = accounts or NullAccountCenterPort()
        self.browsers = browsers or NullBrowserRuntimePort()
        self.proxies = proxies or NullProxyCenterPort()
        self.farming = farming or NullFarmingPort()
        self.concurrency_limit = concurrency_limit
        self.approval_required = approval_required
        self.projects: dict[str, ContentProject] = {}
        self.media: dict[str, MediaAsset] = {}
        self.drafts: dict[str, ContentDraft] = {}
        self.captions: dict[str, Caption] = {}
        self.hashtags: dict[str, HashtagSet] = {}
        self.covers: dict[str, Cover] = {}
        self.schedules: dict[str, PublishingSchedule] = {}
        self.templates: dict[str, ContentTemplate] = {}
        self.queue: dict[str, PublishJob] = {}
        self.publishing_history: list[dict[str, Any]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = ContentMetrics()

    @staticmethod
    def _require(scope: ContentScope, action: str) -> None:
        permission = f"tiktok:content:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:content:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: ContentScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError(
                "Cross-tenant or cross-workspace content access denied."
            )

    def _audit(self, action: str, resource: str, scope: ContentScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )

    def create_project(
        self, project: ContentProject, scope: ContentScope
    ) -> ContentProject:
        self._require(scope, "write")
        self._scoped(project, scope)
        project.validate()
        if project.id in self.projects:
            raise ValueError("Project ID must be unique.")
        self.projects[project.id] = project
        self.metrics.increment("tiktok_content_projects_total")
        self._audit("project.create", project.id, scope)
        return project

    def list_projects(self, scope: ContentScope) -> list[ContentProject]:
        self._require(scope, "read")
        return [
            project
            for project in self.projects.values()
            if project.tenant == scope.tenant
            and project.workspace == scope.workspace
            and project.status is not ProjectStatus.DELETED
        ]

    def transition(
        self, project_reference: str, status: ProjectStatus, scope: ContentScope
    ) -> ContentProject:
        self._require(scope, "write")
        project = self.projects[project_reference]
        self._scoped(project, scope)
        transitions = {
            ProjectStatus.DRAFT: {
                ProjectStatus.EDITING,
                ProjectStatus.ARCHIVED,
                ProjectStatus.DELETED,
            },
            ProjectStatus.EDITING: {
                ProjectStatus.DRAFT,
                ProjectStatus.READY,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.READY: {
                ProjectStatus.EDITING,
                ProjectStatus.QUEUED,
                ProjectStatus.SCHEDULED,
            },
            ProjectStatus.QUEUED: {
                ProjectStatus.PUBLISHING,
                ProjectStatus.PAUSED,
                ProjectStatus.READY,
            },
            ProjectStatus.SCHEDULED: {
                ProjectStatus.QUEUED,
                ProjectStatus.PAUSED,
                ProjectStatus.READY,
            },
            ProjectStatus.PUBLISHING: {
                ProjectStatus.PUBLISHED,
                ProjectStatus.PAUSED,
                ProjectStatus.READY,
            },
            ProjectStatus.PUBLISHED: {ProjectStatus.ARCHIVED},
            ProjectStatus.PAUSED: {
                ProjectStatus.READY,
                ProjectStatus.QUEUED,
                ProjectStatus.ARCHIVED,
            },
            ProjectStatus.ARCHIVED: {ProjectStatus.DRAFT, ProjectStatus.DELETED},
            ProjectStatus.DELETED: set(),
        }
        if status not in transitions[project.status]:
            raise ValueError(
                f"Invalid content transition: {project.status.value} -> {status.value}"
            )
        project.status = status
        project.version += 1
        project.updated_at = utcnow()
        self._audit(f"project.{status.value}", project.id, scope)
        return project

    def add_media(self, asset: MediaAsset, scope: ContentScope) -> MediaAsset:
        self._require(scope, "upload")
        self._scoped(asset, scope)
        asset.validate()
        duplicate = next(
            (
                value
                for value in self.media.values()
                if value.tenant == scope.tenant
                and value.workspace == scope.workspace
                and value.checksum == asset.checksum
            ),
            None,
        )
        if duplicate is not None:
            return duplicate
        if asset.id in self.media:
            raise ValueError("Media ID must be unique.")
        self.media[asset.id] = asset
        self.metrics.increment("tiktok_media_assets_total")
        self._audit("media.add", asset.id, scope)
        return asset

    def create_draft(self, draft: ContentDraft, scope: ContentScope) -> ContentDraft:
        self._require(scope, "write")
        self._scoped(draft, scope)
        project = self.projects[draft.project_reference]
        self._scoped(project, scope)
        for reference in draft.media_references:
            self._scoped(self.media[reference], scope)
        if draft.id in self.drafts:
            raise ValueError("Draft ID must be unique.")
        draft.versions.append(DraftVersion(1, {"title": draft.title}, scope.actor))
        self.drafts[draft.id] = draft
        self.metrics.increment("tiktok_drafts_total")
        self._audit("draft.create", draft.id, scope)
        return draft

    def edit_draft(
        self, reference: str, scope: ContentScope, **changes: Any
    ) -> ContentDraft:
        self._require(scope, "write")
        draft = self.drafts[reference]
        self._scoped(draft, scope)
        allowed = {"title", "media_references"}
        if set(changes) - allowed:
            raise ValueError("Unsupported draft field.")
        for key, value in changes.items():
            setattr(draft, key, value)
        draft.version += 1
        draft.versions.append(
            DraftVersion(draft.version, deepcopy(changes), scope.actor)
        )
        self._audit("draft.edit", draft.id, scope)
        return draft

    def duplicate_draft(
        self, reference: str, new_reference: str, scope: ContentScope
    ) -> ContentDraft:
        source = self.drafts[reference]
        self._scoped(source, scope)
        clone = ContentDraft(
            new_reference,
            source.project_reference,
            scope.tenant,
            scope.workspace,
            f"{source.title} (copy)",
            list(source.media_references),
        )
        return self.create_draft(clone, scope)

    def archive_draft(
        self, reference: str, scope: ContentScope, *, archived: bool = True
    ) -> ContentDraft:
        self._require(scope, "write")
        draft = self.drafts[reference]
        self._scoped(draft, scope)
        draft.archived = archived
        self._audit("draft.archive" if archived else "draft.restore", draft.id, scope)
        return draft

    def review_draft(
        self,
        reference: str,
        scope: ContentScope,
        *,
        review: ReviewStatus,
        approval: ApprovalStatus,
    ) -> ContentDraft:
        self._require(scope, "approve")
        draft = self.drafts[reference]
        self._scoped(draft, scope)
        draft.review_status = review
        draft.approval_status = approval
        self._audit("draft.review", draft.id, scope)
        return draft

    def save_caption(self, caption: Caption, scope: ContentScope) -> Caption:
        self._require(scope, "write")
        self._scoped(caption, scope)
        self._scoped(self.drafts[caption.draft_reference], scope)
        caption.validate()
        self.captions[caption.id] = caption
        self._audit("caption.save", caption.id, scope)
        return caption

    def save_hashtags(self, hashtags: HashtagSet, scope: ContentScope) -> HashtagSet:
        self._require(scope, "write")
        self._scoped(hashtags, scope)
        hashtags.validate()
        self.hashtags[hashtags.id] = hashtags
        self._audit("hashtags.save", hashtags.id, scope)
        return hashtags

    def save_cover(self, cover: Cover, scope: ContentScope) -> Cover:
        self._require(scope, "upload")
        self._scoped(cover, scope)
        self._scoped(self.drafts[cover.draft_reference], scope)
        cover.validate()
        previous = self.covers.get(cover.id)
        if previous:
            cover.history = previous.history + [previous.encrypted_storage_reference]
        self.covers[cover.id] = cover
        self._audit("cover.save", cover.id, scope)
        return cover

    def create_schedule(
        self, schedule: PublishingSchedule, scope: ContentScope
    ) -> PublishingSchedule:
        self._require(scope, "schedule")
        self._scoped(schedule, scope)
        self._scoped(self.projects[schedule.project_reference], scope)
        schedule.validate()
        self.schedules[schedule.id] = schedule
        self._audit("schedule.create", schedule.id, scope)
        return schedule

    def save_template(
        self, template: ContentTemplate, scope: ContentScope
    ) -> ContentTemplate:
        self._require(scope, "write")
        self._scoped(template, scope)
        if not template.id or not template.name or template.version < 1:
            raise ValueError("Template identity and positive version are required.")
        self.templates[template.id] = template
        self._audit("template.save", template.id, scope)
        return template

    def clone_template(
        self, reference: str, new_reference: str, scope: ContentScope
    ) -> ContentTemplate:
        source = self.templates[reference]
        self._scoped(source, scope)
        clone = deepcopy(source)
        clone.id = new_reference
        clone.name = f"{source.name} (copy)"
        clone.imported = False
        return self.save_template(clone, scope)

    def export_template(self, reference: str, scope: ContentScope) -> dict[str, Any]:
        self._require(scope, "read")
        template = self.templates[reference]
        self._scoped(template, scope)
        value = asdict(template)
        value["kind"] = template.kind.value
        return value

    def enqueue(self, job: PublishJob, scope: ContentScope) -> PublishJob:
        self._require(scope, "publish")
        self._scoped(job, scope)
        job.validate()
        project = self.projects[job.project_reference]
        draft = self.drafts[job.draft_reference]
        self._scoped(project, scope)
        self._scoped(draft, scope)
        if (
            self.approval_required
            and draft.approval_status is not ApprovalStatus.APPROVED
        ):
            raise PermissionError("Approved draft required for publishing.")
        if not self.accounts.validate(
            job.account_reference, scope.tenant, scope.workspace
        ):
            raise ValueError("TikTok Account Center rejected the account reference.")
        self.queue[job.id] = job
        target = (
            ProjectStatus.SCHEDULED if job.schedule_reference else ProjectStatus.QUEUED
        )
        if project.status is ProjectStatus.READY:
            self.transition(project.id, target, scope)
        self.metrics.increment("tiktok_publish_queue_total")
        self._audit("publish.enqueue", job.id, scope)
        return job

    def cancel(self, reference: str, scope: ContentScope) -> PublishJob:
        self._require(scope, "publish")
        job = self.queue[reference]
        self._scoped(job, scope)
        if job.status not in {QueueStatus.PENDING, QueueStatus.FAILED}:
            raise ValueError("Only pending or failed jobs can be cancelled.")
        job.status = QueueStatus.CANCELLED
        self._audit("publish.cancel", job.id, scope)
        return job

    def process_queue(self, scope: ContentScope) -> list[PublishJob]:
        self._require(scope, "publish")
        pending = sorted(
            (
                job
                for job in self.queue.values()
                if job.tenant == scope.tenant
                and job.workspace == scope.workspace
                and job.status in {QueueStatus.PENDING, QueueStatus.FAILED}
                and job.retries <= job.maximum_retries
            ),
            key=lambda job: (-job.priority, job.created_at),
        )[: self.concurrency_limit]
        for job in pending:
            self._publish(job, scope)
        return pending

    def _publish(self, job: PublishJob, scope: ContentScope) -> None:
        project = self.projects[job.project_reference]
        draft = self.drafts[job.draft_reference]
        started = monotonic()
        job.status = QueueStatus.RUNNING
        job.started_at = utcnow()
        try:
            if not self.farming.allowed(
                job.account_reference, scope.tenant, scope.workspace
            ):
                raise RuntimeError("Account Farming policy paused this account.")
            if not self.proxies.healthy_for(
                job.account_reference, scope.tenant, scope.workspace
            ):
                raise RuntimeError("Proxy Center has no healthy scoped route.")
            if project.status in {ProjectStatus.QUEUED, ProjectStatus.SCHEDULED}:
                self.transition(project.id, ProjectStatus.PUBLISHING, scope)
            payload = {
                "project_reference": project.id,
                "draft_reference": draft.id,
                "media_references": list(draft.media_references),
            }
            if not self.browsers.publish(
                job.account_reference, payload, scope.tenant, scope.workspace
            ):
                raise RuntimeError("Browser Runtime publishing failed.")
            job.status = QueueStatus.SUCCEEDED
            project.status = ProjectStatus.PUBLISHED
            project.version += 1
            self.metrics.increment("tiktok_publish_success_total")
        except Exception as error:
            job.status = QueueStatus.FAILED
            job.retries += 1
            job.failure_reason = type(error).__name__
            project.status = ProjectStatus.READY
            self.metrics.increment("tiktok_publish_failures_total")
        finally:
            job.finished_at = utcnow()
            elapsed = monotonic() - started
            self.metrics.set("tiktok_publish_latency_seconds", elapsed)
            self.publishing_history.append(
                {
                    "job": job.id,
                    "project": project.id,
                    "status": job.status.value,
                    "attempt": job.retries + 1,
                    "occurred_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._audit(f"publish.{job.status.value}", job.id, scope)

    def dashboard(self, scope: ContentScope) -> dict[str, Any]:
        self._require(scope, "read")
        def scoped(values: Any) -> list[Any]:
            return [
                value
                for value in values
                if value.tenant == scope.tenant
                and value.workspace == scope.workspace
            ]

        jobs = scoped(self.queue.values())
        return {
            "sections": [
                "Projects",
                "Media",
                "Drafts",
                "Queue",
                "Schedules",
                "Templates",
                "Publishing",
                "Analytics",
                "Failures",
                "Statistics",
            ],
            "projects": len(scoped(self.projects.values())),
            "media": len(scoped(self.media.values())),
            "drafts": len(scoped(self.drafts.values())),
            "queue": len(jobs),
            "schedules": len(scoped(self.schedules.values())),
            "templates": len(scoped(self.templates.values())),
            "failures": sum(job.status is QueueStatus.FAILED for job in jobs),
            "statistics": self.metrics.snapshot(),
        }

    def analytics(self, scope: ContentScope) -> dict[str, Any]:
        dashboard = self.dashboard(scope)
        jobs = [
            job
            for job in self.queue.values()
            if job.tenant == scope.tenant and job.workspace == scope.workspace
        ]
        succeeded = sum(job.status is QueueStatus.SUCCEEDED for job in jobs)
        failed = sum(job.status is QueueStatus.FAILED for job in jobs)
        completed = succeeded + failed
        return {
            "publishing_history": [
                event
                for event in self.publishing_history
                if event["job"] in {job.id for job in jobs}
            ],
            "queue_statistics": {"total": len(jobs), "pending": len(jobs) - completed},
            "success_rate": succeeded / completed if completed else 0.0,
            "failure_rate": failed / completed if completed else 0.0,
            "processing_time": self.metrics.snapshot()[
                "tiktok_publish_latency_seconds"
            ],
            "content_inventory": {
                "projects": dashboard["projects"],
                "media": dashboard["media"],
                "drafts": dashboard["drafts"],
            },
        }
