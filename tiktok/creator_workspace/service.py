"""Enterprise TikTok Creator Workspace coordination service."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from datetime import datetime
from time import monotonic
from typing import Any

from .adapters import (
    AnalyticsCenterPort,
    ContentCenterPort,
    CoordinationPort,
    NullAnalyticsCenter,
    NullContentCenter,
    NullCoordinationPort,
    NullPublishingCenter,
    PublishingCenterPort,
)
from .metrics import CreatorMetrics
from .models import (
    Approval,
    ApprovalKind,
    ApprovalStatus,
    CalendarEntry,
    ContentProject,
    CreativeAsset,
    CreatorScope,
    CreatorTemplate,
    CreatorWorkspace,
    PublishingPlanRequest,
    Review,
    ReviewStatus,
    WorkspaceStatus,
    utcnow,
)


class TikTokCreatorWorkspace:
    """Tenant-isolated creative control plane; execution stays delegated."""

    def __init__(
        self,
        *,
        content: ContentCenterPort | None = None,
        publishing: PublishingCenterPort | None = None,
        analytics_center: AnalyticsCenterPort | None = None,
        workflow: CoordinationPort | None = None,
        automation: CoordinationPort | None = None,
        decision: CoordinationPort | None = None,
        runtime: CoordinationPort | None = None,
    ) -> None:
        self.content = content or NullContentCenter()
        self.publishing = publishing or NullPublishingCenter()
        self.analytics_center = analytics_center or NullAnalyticsCenter()
        self.workflow = workflow or NullCoordinationPort()
        self.automation = automation or NullCoordinationPort()
        self.decision = decision or NullCoordinationPort()
        self.runtime = runtime or NullCoordinationPort()
        self.workspaces: dict[str, CreatorWorkspace] = {}
        self.projects: dict[str, ContentProject] = {}
        self.assets: dict[str, CreativeAsset] = {}
        self.calendar_entries: dict[str, CalendarEntry] = {}
        self.templates: dict[str, CreatorTemplate] = {}
        self.reviews: dict[str, Review] = {}
        self.approvals: dict[str, Approval] = {}
        self.publish_plans: list[dict[str, str]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = CreatorMetrics()

    @staticmethod
    def _require(scope: CreatorScope, action: str) -> None:
        permission = f"tiktok:creator:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:creator:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: CreatorScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _audit(self, action: str, resource: str, scope: CreatorScope) -> None:
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

    def _measure(self, started: float) -> None:
        self.metrics.set("tiktok_creator_latency_seconds", monotonic() - started)

    @staticmethod
    def _visible(values: Iterable[Any], scope: CreatorScope) -> list[Any]:
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    def create_workspace(
        self, workspace: CreatorWorkspace, scope: CreatorScope
    ) -> CreatorWorkspace:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(workspace, scope)
        workspace.validate()
        if workspace.id in self.workspaces:
            raise ValueError("Workspace ID must be unique.")
        self.workspaces[workspace.id] = workspace
        self._audit("workspace.create", workspace.id, scope)
        self._measure(started)
        return workspace

    def list_workspaces(self, scope: CreatorScope) -> list[CreatorWorkspace]:
        self._require(scope, "read")
        return [
            item
            for item in self._visible(self.workspaces.values(), scope)
            if item.status is not WorkspaceStatus.DELETED
        ]

    def create_project(
        self, project: ContentProject, scope: CreatorScope
    ) -> ContentProject:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(project, scope)
        project.validate()
        workspace = self.workspaces[project.creator_workspace_id]
        self._scoped(workspace, scope)
        if project.workflow_reference and not self.workflow.reference_exists(
            project.workflow_reference, scope.tenant, scope.workspace
        ):
            raise ValueError("Workflow reference was not found in Workflow Center.")
        if project.id in self.projects:
            raise ValueError("Project ID must be unique.")
        self.projects[project.id] = project
        self.metrics.increment("tiktok_creator_projects_total")
        self._audit("project.create", project.id, scope)
        self._measure(started)
        return project

    def list_projects(self, scope: CreatorScope) -> list[ContentProject]:
        self._require(scope, "read")
        return [
            item
            for item in self._visible(self.projects.values(), scope)
            if item.status is not WorkspaceStatus.DELETED
        ]

    def transition(
        self, reference: str, status: WorkspaceStatus, scope: CreatorScope
    ) -> ContentProject:
        self._require(scope, "write")
        project = self.projects[reference]
        self._scoped(project, scope)
        transitions = {
            WorkspaceStatus.DRAFT: {
                WorkspaceStatus.PLANNING,
                WorkspaceStatus.ARCHIVED,
                WorkspaceStatus.DELETED,
            },
            WorkspaceStatus.PLANNING: {
                WorkspaceStatus.EDITING,
                WorkspaceStatus.ARCHIVED,
            },
            WorkspaceStatus.EDITING: {
                WorkspaceStatus.REVIEW,
                WorkspaceStatus.PLANNING,
            },
            WorkspaceStatus.REVIEW: {
                WorkspaceStatus.EDITING,
                WorkspaceStatus.APPROVED,
            },
            WorkspaceStatus.APPROVED: {
                WorkspaceStatus.SCHEDULED,
                WorkspaceStatus.EDITING,
            },
            WorkspaceStatus.SCHEDULED: {
                WorkspaceStatus.PUBLISHED,
                WorkspaceStatus.APPROVED,
            },
            WorkspaceStatus.PUBLISHED: {WorkspaceStatus.ARCHIVED},
            WorkspaceStatus.ARCHIVED: {
                WorkspaceStatus.DRAFT,
                WorkspaceStatus.DELETED,
            },
            WorkspaceStatus.DELETED: set(),
        }
        if status not in transitions[project.status]:
            raise ValueError(
                f"Invalid creator lifecycle: {project.status.value} -> {status.value}"
            )
        if status is WorkspaceStatus.APPROVED and not self._has_approval(
            project.id, ApprovalKind.CONTENT, scope
        ):
            raise PermissionError("Active content approval is required.")
        project.status = status
        project.version += 1
        project.updated_at = utcnow()
        self._audit(f"project.{status.value}", project.id, scope)
        return project

    def add_asset(self, asset: CreativeAsset, scope: CreatorScope) -> CreativeAsset:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(asset, scope)
        asset.validate()
        self._scoped(self.projects[asset.project_reference], scope)
        if asset.id in self.assets:
            raise ValueError("Asset ID must be unique.")
        self.assets[asset.id] = asset
        self.metrics.increment("tiktok_creator_assets_total")
        self._audit("asset.create", asset.id, scope)
        self._measure(started)
        return asset

    def list_assets(self, scope: CreatorScope) -> list[CreativeAsset]:
        self._require(scope, "read")
        return self._visible(self.assets.values(), scope)

    def add_calendar_entry(
        self, entry: CalendarEntry, scope: CreatorScope
    ) -> CalendarEntry:
        self._require(scope, "schedule")
        self._scoped(entry, scope)
        entry.validate()
        self._scoped(self.projects[entry.project_reference], scope)
        if entry.id in self.calendar_entries:
            raise ValueError("Calendar entry ID must be unique.")
        self.calendar_entries[entry.id] = entry
        self._audit("calendar.create", entry.id, scope)
        return entry

    def calendar(
        self,
        scope: CreatorScope,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[CalendarEntry]:
        self._require(scope, "read")
        entries = self._visible(self.calendar_entries.values(), scope)
        return [
            entry
            for entry in entries
            if (start is None or entry.starts_at >= start)
            and (end is None or entry.starts_at < end)
        ]

    def save_template(
        self, template: CreatorTemplate, scope: CreatorScope
    ) -> CreatorTemplate:
        self._require(scope, "write")
        self._scoped(template, scope)
        template.validate()
        self.templates[template.id] = template
        self._audit("template.save", template.id, scope)
        return template

    def clone_template(
        self, reference: str, new_reference: str, scope: CreatorScope
    ) -> CreatorTemplate:
        source = self.templates[reference]
        self._scoped(source, scope)
        clone = deepcopy(source)
        clone.id = new_reference
        clone.name = f"{source.name} (copy)"
        clone.version = 1
        clone.source_reference = source.id
        return self.save_template(clone, scope)

    def request_review(self, review: Review, scope: CreatorScope) -> Review:
        self._require(scope, "review")
        self._scoped(review, scope)
        project = self.projects[review.project_reference]
        self._scoped(project, scope)
        if project.status is not WorkspaceStatus.REVIEW:
            raise ValueError("Project must be in review before requesting a review.")
        review.history.append(
            {
                "status": review.status.value,
                "actor": scope.actor,
                "occurred_at": utcnow().isoformat(),
            }
        )
        self.reviews[review.id] = review
        self.metrics.increment("tiktok_creator_reviews_total")
        self._audit("review.request", review.id, scope)
        return review

    def complete_review(
        self,
        reference: str,
        status: ReviewStatus,
        notes: str,
        scope: CreatorScope,
    ) -> Review:
        self._require(scope, "review")
        review = self.reviews[reference]
        self._scoped(review, scope)
        review.status = status
        review.notes = notes
        review.completed_at = utcnow()
        review.history.append(
            {
                "status": status.value,
                "actor": scope.actor,
                "occurred_at": review.completed_at.isoformat(),
            }
        )
        self._audit("review.complete", review.id, scope)
        return review

    def decide_approval(self, approval: Approval, scope: CreatorScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        self._scoped(self.projects[approval.project_reference], scope)
        if approval.status is ApprovalStatus.APPROVED and (
            approval.expires_at is not None and approval.expires_at <= utcnow()
        ):
            raise ValueError("An approval cannot be granted with a past expiration.")
        approval.decided_at = utcnow()
        self.approvals[approval.id] = approval
        self.metrics.increment("tiktok_creator_approvals_total")
        self._audit(f"approval.{approval.status.value}", approval.id, scope)
        return approval

    def _has_approval(
        self, project: str, kind: ApprovalKind, scope: CreatorScope
    ) -> bool:
        return any(
            item.project_reference == project
            and item.kind is kind
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.active
            for item in self.approvals.values()
        )

    def submit_publish_plan(self, reference: str, scope: CreatorScope) -> str:
        started = monotonic()
        self._require(scope, "publish")
        project = self.projects[reference]
        self._scoped(project, scope)
        if project.status is not WorkspaceStatus.APPROVED:
            raise PermissionError("Project must be approved before scheduling.")
        if not project.publishing_plan_reference:
            raise ValueError("Publishing plan reference is required.")
        if not self._has_approval(reference, ApprovalKind.PUBLISHING, scope):
            raise PermissionError("Active publishing approval is required.")
        request = PublishingPlanRequest(
            reference,
            project.publishing_plan_reference,
            scope.tenant,
            scope.workspace,
            scope.actor,
        )
        result = self.publishing.submit_plan(request)
        project.status = WorkspaceStatus.SCHEDULED
        project.version += 1
        project.updated_at = utcnow()
        self.publish_plans.append(
            {
                "project": project.id,
                "plan": project.publishing_plan_reference,
                "result": result,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )
        self.metrics.increment("tiktok_creator_publish_plan_total")
        self._audit("publishing_plan.submit", project.id, scope)
        self._measure(started)
        return result

    def reviews_for(self, scope: CreatorScope) -> list[Review]:
        self._require(scope, "read")
        return self._visible(self.reviews.values(), scope)

    def approvals_for(self, scope: CreatorScope) -> list[Approval]:
        self._require(scope, "read")
        return self._visible(self.approvals.values(), scope)

    def analytics(self, scope: CreatorScope) -> dict[str, Any]:
        self._require(scope, "read")
        projects = self.list_projects(scope)
        assets = self.list_assets(scope)
        reviews = self.reviews_for(scope)
        approvals = self.approvals_for(scope)
        completed_reviews = [
            review for review in reviews if review.completed_at is not None
        ]
        decided_approvals = [
            approval for approval in approvals if approval.decided_at is not None
        ]

        def average_seconds(values: list[tuple[datetime, datetime]]) -> float:
            if not values:
                return 0.0
            return sum((end - start).total_seconds() for start, end in values) / len(
                values
            )

        return {
            "workspace_kpis": {
                "projects": len(projects),
                "scheduled": sum(
                    item.status is WorkspaceStatus.SCHEDULED for item in projects
                ),
                "published": sum(
                    item.status is WorkspaceStatus.PUBLISHED for item in projects
                ),
            },
            "publishing_statistics": self.analytics_center.workspace_statistics(
                scope.tenant, scope.workspace
            ),
            "content_inventory": {
                "projects": len(projects),
                "assets": len(assets),
                "templates": len(self._visible(self.templates.values(), scope)),
            },
            "review_time_seconds": average_seconds(
                [
                    (item.requested_at, item.completed_at)
                    for item in completed_reviews
                    if item.completed_at is not None
                ]
            ),
            "approval_time_seconds": average_seconds(
                [
                    (item.requested_at, item.decided_at)
                    for item in decided_approvals
                    if item.decided_at is not None
                ]
            ),
            "productivity": {
                "approved": sum(item.active for item in approvals),
                "completed_reviews": len(completed_reviews),
                "publish_plans": sum(
                    event["tenant"] == scope.tenant
                    and event["workspace"] == scope.workspace
                    for event in self.publish_plans
                ),
            },
        }

    def dashboard(self, scope: CreatorScope) -> dict[str, Any]:
        return {
            "sections": [
                "Workspace Overview",
                "Projects",
                "Calendar",
                "Assets",
                "Drafts",
                "Templates",
                "Reviews",
                "Approvals",
                "Analytics",
            ],
            "workspaces": len(self.list_workspaces(scope)),
            "projects": len(self.list_projects(scope)),
            "calendar": len(self.calendar(scope)),
            "assets": len(self.list_assets(scope)),
            "templates": len(self._visible(self.templates.values(), scope)),
            "reviews": len(self.reviews_for(scope)),
            "approvals": len(self.approvals_for(scope)),
            "analytics": self.analytics(scope),
            "metrics": self.metrics.snapshot(),
        }
