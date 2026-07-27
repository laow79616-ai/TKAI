from __future__ import annotations

from datetime import datetime, timezone

import pytest

from tiktok.content_center import (
    METRICS,
    ApprovalStatus,
    Caption,
    CaptionMode,
    ContentDraft,
    ContentProject,
    ContentScope,
    ContentTemplate,
    Cover,
    HashtagSet,
    MediaAsset,
    MediaType,
    MissedRunPolicy,
    ProjectStatus,
    PublishingSchedule,
    PublishJob,
    QueueMode,
    QueueStatus,
    ReviewStatus,
    ScheduleKind,
    TemplateKind,
    TikTokContentCenter,
)


@pytest.fixture
def scope():
    return ContentScope(
        "tenant-a", "workspace-a", "editor", frozenset({"tiktok:content:admin"})
    )


@pytest.fixture
def center(scope):
    value = TikTokContentCenter(concurrency_limit=2)
    value.create_project(
        ContentProject(
            "project-1",
            "Launch",
            "TikTok launch content",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "campaign",
        ),
        scope,
    )
    return value


def test_project_lifecycle_versioning_and_isolation(center, scope):
    project = center.projects["project-1"]
    for status in (ProjectStatus.EDITING, ProjectStatus.READY):
        center.transition(project.id, status, scope)
    assert project.version == 3
    assert center.list_projects(ContentScope("tenant-a", "other", "viewer")) == []
    with pytest.raises(PermissionError):
        center.transition(
            project.id, ProjectStatus.QUEUED, ContentScope("tenant-b", "other", "x")
        )
    with pytest.raises(ValueError, match="Invalid"):
        center.transition(project.id, ProjectStatus.PUBLISHED, scope)


def test_media_deduplication_and_encrypted_references(center, scope):
    asset = MediaAsset(
        "media-1",
        scope.tenant,
        scope.workspace,
        "video.mp4",
        MediaType.VIDEO,
        "sha256:abc",
        "kms://bucket/object",
        "campaign",
        {"launch"},
    )
    assert center.add_media(asset, scope) is asset
    duplicate = MediaAsset(
        "media-2",
        scope.tenant,
        scope.workspace,
        "duplicate.mp4",
        MediaType.VIDEO,
        "sha256:abc",
        "vault://other/object",
    )
    assert center.add_media(duplicate, scope) is asset
    assert len(center.media) == 1
    with pytest.raises(ValueError, match="encrypted"):
        center.add_media(
            MediaAsset(
                "bad",
                scope.tenant,
                scope.workspace,
                "bad.mp4",
                MediaType.VIDEO,
                "sha256:bad",
                "file:///secret",
            ),
            scope,
        )


def test_drafts_versions_duplicate_archive_restore_and_review(center, scope):
    draft = center.create_draft(
        ContentDraft(
            "draft-1",
            "project-1",
            scope.tenant,
            scope.workspace,
            "First cut",
        ),
        scope,
    )
    center.edit_draft(draft.id, scope, title="Second cut")
    assert draft.version == 2 and len(draft.versions) == 2
    clone = center.duplicate_draft(draft.id, "draft-2", scope)
    assert clone.title.endswith("(copy)")
    center.archive_draft(draft.id, scope)
    assert draft.archived
    center.archive_draft(draft.id, scope, archived=False)
    assert not draft.archived
    center.review_draft(
        draft.id,
        scope,
        review=ReviewStatus.APPROVED,
        approval=ApprovalStatus.APPROVED,
    )
    assert draft.approval_status is ApprovalStatus.APPROVED


def test_captions_hashtags_and_covers(center, scope):
    center.create_draft(
        ContentDraft("draft-1", "project-1", scope.tenant, scope.workspace, "Content"),
        scope,
    )
    caption = Caption(
        "caption-1",
        "draft-1",
        scope.tenant,
        scope.workspace,
        "Hello {name}",
        CaptionMode.TEMPLATE_BASED,
        {"name": "world"},
        "en-US",
        template_reference="template-1",
    )
    assert center.save_caption(caption, scope).character_count == 12
    with pytest.raises(ValueError):
        center.save_hashtags(
            HashtagSet(
                "hashtags-bad", scope.tenant, scope.workspace, "Bad", ["not-a-tag"]
            ),
            scope,
        )
    tags = HashtagSet(
        "hashtags-1",
        scope.tenant,
        scope.workspace,
        "Launch",
        ["#launch", "#product"],
        favorite=True,
        collection="campaigns",
        ranking_reference="analytics://rankings/launch",
    )
    assert center.save_hashtags(tags, scope) is tags
    first = Cover(
        "cover-1",
        "draft-1",
        scope.tenant,
        scope.workspace,
        "kms://covers/v1",
    )
    center.save_cover(first, scope)
    second = Cover(
        "cover-1",
        "draft-1",
        scope.tenant,
        scope.workspace,
        "kms://covers/v2",
        approval_status=ApprovalStatus.APPROVED,
    )
    center.save_cover(second, scope)
    assert second.history == ["kms://covers/v1"]


def test_schedules_templates_import_export_and_clone(center, scope):
    schedule = PublishingSchedule(
        "schedule-1",
        "project-1",
        scope.tenant,
        scope.workspace,
        ScheduleKind.ONE_TIME,
        "Asia/Shanghai",
        ("09:00", "11:00"),
        MissedRunPolicy.RUN_ONCE,
        datetime.now(timezone.utc),
        calendar_reference="calendar://marketing",
    )
    assert center.create_schedule(schedule, scope) is schedule
    template = ContentTemplate(
        "template-1",
        scope.tenant,
        scope.workspace,
        "Caption base",
        TemplateKind.CAPTION,
        {"text": "Hello {name}"},
        imported=True,
    )
    center.save_template(template, scope)
    assert center.export_template(template.id, scope)["kind"] == "caption"
    clone = center.clone_template(template.id, "template-2", scope)
    assert not clone.imported and clone.content == template.content


def _approved_draft(center, scope):
    draft = center.create_draft(
        ContentDraft("draft-1", "project-1", scope.tenant, scope.workspace, "Approved"),
        scope,
    )
    center.review_draft(
        draft.id,
        scope,
        review=ReviewStatus.APPROVED,
        approval=ApprovalStatus.APPROVED,
    )
    center.transition("project-1", ProjectStatus.EDITING, scope)
    center.transition("project-1", ProjectStatus.READY, scope)
    return draft


def test_queue_approval_retry_cancellation_metrics_and_analytics(center, scope):
    _approved_draft(center, scope)
    job = PublishJob(
        "job-1",
        "project-1",
        "draft-1",
        "account-1",
        scope.tenant,
        scope.workspace,
        QueueMode.IMMEDIATE,
        priority=90,
    )
    center.enqueue(job, scope)
    assert center.process_queue(scope) == [job]
    assert job.status is QueueStatus.SUCCEEDED
    analytics = center.analytics(scope)
    assert analytics["success_rate"] == 1
    assert analytics["content_inventory"]["projects"] == 1
    assert set(center.metrics.snapshot()) == set(METRICS)

    center.projects["project-1"].status = ProjectStatus.READY
    second = PublishJob(
        "job-2",
        "project-1",
        "draft-1",
        "account-1",
        scope.tenant,
        scope.workspace,
    )
    center.enqueue(second, scope)
    center.cancel(second.id, scope)
    assert second.status is QueueStatus.CANCELLED


def test_approval_enforcement_dashboard_api_and_no_live_tiktok(scope):
    center = TikTokContentCenter()
    center.create_project(
        ContentProject(
            "p", "Project", "", scope.tenant, scope.workspace, scope.actor, "general"
        ),
        scope,
    )
    center.create_draft(
        ContentDraft("d", "p", scope.tenant, scope.workspace, "Draft"), scope
    )
    center.transition("p", ProjectStatus.EDITING, scope)
    center.transition("p", ProjectStatus.READY, scope)
    with pytest.raises(PermissionError, match="Approved"):
        center.enqueue(
            PublishJob("j", "p", "d", "account", scope.tenant, scope.workspace),
            scope,
        )
    assert {"Projects", "Queue", "Failures", "Statistics"} <= set(
        center.dashboard(scope)["sections"]
    )

    from tiktok.content_center.api import ROUTES, register_content_center_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, methods, tags):
            self.routes.append((path, methods, endpoint, tags))

    app = App()
    register_content_center_routes(app, center)
    assert set(ROUTES) <= {route[0] for route in app.routes}


def test_validation_rejects_secrets_and_other_platform_metadata(scope):
    for key in ("secret", "token", "password", "cookie", "credential"):
        with pytest.raises(ValueError):
            ContentProject(
                "p",
                "Project",
                "",
                scope.tenant,
                scope.workspace,
                scope.actor,
                "general",
                metadata={key: "redacted"},
            ).validate()
