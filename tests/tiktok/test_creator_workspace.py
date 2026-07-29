"""Offline coverage for the Enterprise TikTok Creator Workspace."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tiktok.creator_workspace import (
    Approval,
    ApprovalKind,
    ApprovalStatus,
    AssetKind,
    CalendarEntry,
    CalendarKind,
    ContentProject,
    CreativeAsset,
    CreatorScope,
    CreatorTemplate,
    CreatorWorkspace,
    Review,
    ReviewStatus,
    TemplateKind,
    WorkspaceStatus,
)
from tiktok.creator_workspace.adapters import NullPublishingCenter
from tiktok.creator_workspace.api import ROUTES, register_creator_workspace_routes
from tiktok.creator_workspace.metrics import METRIC_NAMES
from tiktok.creator_workspace.models import utcnow
from tiktok.creator_workspace.service import TikTokCreatorWorkspace


def scope(workspace: str = "workspace") -> CreatorScope:
    return CreatorScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:creator:admin"}),
    )


def workspace() -> CreatorWorkspace:
    return CreatorWorkspace(
        "workspace-1",
        "Creator team",
        "Local creative planning",
        "operator",
        "tenant",
        "workspace",
    )


def project() -> ContentProject:
    return ContentProject(
        "project-1",
        "workspace-1",
        "Launch video",
        "tenant",
        "workspace",
        "operator",
        campaign_reference="campaign://launch",
        publishing_plan_reference="plan-1",
        workflow_reference="workflow-1",
    )


def ready_center() -> tuple[TikTokCreatorWorkspace, NullPublishingCenter]:
    publisher = NullPublishingCenter()
    center = TikTokCreatorWorkspace(publishing=publisher)
    center.create_workspace(workspace(), scope())
    center.create_project(project(), scope())
    return center, publisher


def move_to_review(center: TikTokCreatorWorkspace) -> None:
    center.transition("project-1", WorkspaceStatus.PLANNING, scope())
    center.transition("project-1", WorkspaceStatus.EDITING, scope())
    center.transition("project-1", WorkspaceStatus.REVIEW, scope())


def approve(center: TikTokCreatorWorkspace, kind: ApprovalKind, reference: str) -> None:
    center.decide_approval(
        Approval(
            reference,
            "project-1",
            "tenant",
            "workspace",
            kind,
            "reviewer",
            ApprovalStatus.APPROVED,
            utcnow() + timedelta(hours=1),
            "approved",
        ),
        scope(),
    )


def test_workspace_project_lifecycle_and_version_history() -> None:
    center, _ = ready_center()
    move_to_review(center)
    with pytest.raises(PermissionError, match="content approval"):
        center.transition("project-1", WorkspaceStatus.APPROVED, scope())
    approve(center, ApprovalKind.CONTENT, "content-approval")
    result = center.transition("project-1", WorkspaceStatus.APPROVED, scope())
    assert result.version == 5
    assert [event["action"] for event in center.audit][-1] == "project.approved"


def test_encrypted_assets_calendar_views_and_templates() -> None:
    center, _ = ready_center()
    asset = center.add_asset(
        CreativeAsset(
            "asset-1",
            "project-1",
            "tenant",
            "workspace",
            "launch.mp4",
            AssetKind.VIDEO,
            "kms://creative/launch",
        ),
        scope(),
    )
    starts_at = utcnow() + timedelta(days=1)
    entry = center.add_calendar_entry(
        CalendarEntry(
            "calendar-1",
            "project-1",
            "tenant",
            "workspace",
            CalendarKind.REVIEW,
            starts_at,
            "Asia/Shanghai",
            "Final review",
            30,
        ),
        scope(),
    )
    template = center.save_template(
        CreatorTemplate(
            "template-1",
            "tenant",
            "workspace",
            "Launch caption",
            TemplateKind.CAPTION,
            {"caption": "New launch"},
        ),
        scope(),
    )
    clone = center.clone_template("template-1", "template-2", scope())
    assert asset.kind is AssetKind.VIDEO
    assert center.calendar(scope(), start=starts_at - timedelta(minutes=1)) == [entry]
    assert template.version == clone.version == 1
    assert clone.source_reference == "template-1"


def test_asset_encryption_and_metadata_secret_controls() -> None:
    center, _ = ready_center()
    invalid = CreativeAsset(
        "asset-1",
        "project-1",
        "tenant",
        "workspace",
        "launch.mp4",
        AssetKind.VIDEO,
        "file://launch.mp4",
    )
    with pytest.raises(ValueError, match="encrypted"):
        center.add_asset(invalid, scope())
    unsafe = workspace()
    unsafe.metadata = {"token": "never-log-this"}
    with pytest.raises(ValueError, match="Secrets"):
        TikTokCreatorWorkspace().create_workspace(unsafe, scope())


def test_reviews_approvals_and_approval_expiration() -> None:
    center, _ = ready_center()
    move_to_review(center)
    review = center.request_review(
        Review(
            "review-1",
            "project-1",
            "tenant",
            "workspace",
            "reviewer",
        ),
        scope(),
    )
    completed = center.complete_review(
        review.id, ReviewStatus.APPROVED, "ready", scope()
    )
    assert completed.completed_at is not None
    expired = Approval(
        "expired",
        "project-1",
        "tenant",
        "workspace",
        ApprovalKind.CONTENT,
        "reviewer",
        ApprovalStatus.APPROVED,
        utcnow() - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="past expiration"):
        center.decide_approval(expired, scope())


def test_publish_plan_is_approval_gated_and_never_publishes_directly() -> None:
    center, publisher = ready_center()
    move_to_review(center)
    approve(center, ApprovalKind.CONTENT, "content-approval")
    center.transition("project-1", WorkspaceStatus.APPROVED, scope())
    with pytest.raises(PermissionError, match="publishing approval"):
        center.submit_publish_plan("project-1", scope())
    approve(center, ApprovalKind.PUBLISHING, "publishing-approval")
    result = center.submit_publish_plan("project-1", scope())
    assert result == "publishing-plan://plan-1"
    assert len(publisher.submitted) == 1
    assert center.projects["project-1"].status is WorkspaceStatus.SCHEDULED


def test_tenant_workspace_isolation_and_rbac() -> None:
    center = TikTokCreatorWorkspace()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_workspace(workspace(), scope("other"))
    reader = CreatorScope("tenant", "workspace", "reader")
    with pytest.raises(PermissionError, match="write"):
        center.create_workspace(workspace(), reader)


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert callable(endpoint)
        assert tags == ["tiktok-creator-workspace"]
        self.routes.append((path, tuple(methods)))


def test_api_dashboard_analytics_metrics_and_openapi_contracts() -> None:
    center, _ = ready_center()
    app = FakeApp()
    register_creator_workspace_routes(app, center)
    paths = {path for path, _ in app.routes}
    assert set(ROUTES).issubset(paths)
    assert "/tiktok/creator-workspace/dashboard" in paths
    assert "/tiktok/creator-workspace/metrics" in paths
    assert len(center.dashboard(scope())["sections"]) == 9
    assert center.analytics(scope())["content_inventory"]["projects"] == 1
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
