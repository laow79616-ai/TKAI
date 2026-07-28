from datetime import timedelta

import pytest

from tiktok.interaction_center import (
    ApprovalStatus,
    InteractionDraft,
    InteractionProject,
    InteractionScope,
    InteractionTask,
    InteractionTemplate,
    Lifecycle,
    ReviewRecord,
    ReviewStatus,
    TemplateKind,
    TikTokInteractionCenter,
)
from tiktok.interaction_center.models import utcnow


@pytest.fixture
def scope() -> InteractionScope:
    return InteractionScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset({"tiktok:interaction:admin"}),
    )


@pytest.fixture
def center(scope: InteractionScope) -> TikTokInteractionCenter:
    value = TikTokInteractionCenter(concurrency_limit=2)
    value.create_project(
        InteractionProject(
            "p1", "Support", "Reviewed replies", "tenant-a", "workspace-a", "owner"
        ),
        scope,
    )
    value.create_template(
        InteractionTemplate(
            "tpl1",
            "tenant-a",
            "workspace-a",
            "Reply",
            TemplateKind.REPLY,
            {"en": "Hello {name}", "zh": "你好 {name}"},
            {"name"},
        ),
        scope,
    )
    value.create_draft(
        InteractionDraft(
            "d1",
            "p1",
            "tenant-a",
            "workspace-a",
            "Hello Alex",
            "tpl1",
            "en",
            {"name": "Alex"},
        ),
        scope,
    )
    return value


def test_projects_drafts_templates_clone_import_and_history(center, scope):
    assert center.list_projects(scope)[0].priority.value == "normal"
    center.edit_draft("d1", "Hello Sam", {"name": "Sam"}, scope)
    assert center.drafts["d1"].version == 2
    assert len(center.drafts["d1"].history) == 2
    exported = center.export_template("tpl1", scope)
    clone = center.clone_template("tpl1", "tpl2", scope)
    exported["id"] = "tpl3"
    imported = center.import_template(exported, scope)
    assert clone.name.endswith("(copy)")
    assert imported.imported


def test_review_reject_reapprove_expiration_and_audit(center, scope):
    review = center.submit_review(
        ReviewRecord("r1", "d1", "tenant-a", "workspace-a", "reviewer"), scope
    )
    center.decide_review(review.id, False, "Revise tone", scope)
    assert center.drafts["d1"].approval_status is ApprovalStatus.REJECTED
    center.reapprove(review.id, "Approved revision", scope)
    assert center.drafts["d1"].review_status is ReviewStatus.APPROVED
    expired = ReviewRecord(
        "r2",
        "d1",
        "tenant-a",
        "workspace-a",
        "reviewer",
        expires_at=utcnow() - timedelta(seconds=1),
    )
    center.submit_review(expired, scope)
    with pytest.raises(ValueError, match="expired"):
        center.decide_review("r2", True, "", scope)
    assert any(event["action"] == "review.approve" for event in center.audit)


def test_approval_queue_execution_analytics_notifications_and_metrics(center, scope):
    task = center.create_task(
        InteractionTask("task1", "p1", "d1", "tenant-a", "workspace-a", priority=90),
        scope,
    )
    with pytest.raises(PermissionError, match="Approved"):
        center.queue_task(task.id, scope)
    center.submit_review(
        ReviewRecord("r1", "d1", "tenant-a", "workspace-a", "reviewer"), scope
    )
    center.decide_review("r1", True, "Safe", scope)
    assert center.queue_task(task.id, scope).status is Lifecycle.QUEUED
    assert center.run_next(scope).status is Lifecycle.COMPLETED
    analytics = center.analytics(scope)
    assert analytics["task_volume"] == 1
    assert analytics["completion_rate"] == 1
    dashboard = center.dashboard(scope)
    assert {
        "projects",
        "tasks",
        "drafts",
        "templates",
        "reviews",
        "queues",
        "analytics",
        "history",
        "statistics",
    } <= dashboard.keys()
    rendered = center.metrics.render_prometheus()
    for name in center.metrics.NAMES:
        assert name in rendered


def test_tenant_workspace_isolation_and_rbac(center, scope):
    outsider = InteractionScope(
        "tenant-b", "workspace-a", "x", frozenset({"tiktok:interaction:admin"})
    )
    assert center.list_projects(outsider) == []
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.export_template("tpl1", outsider)
    assert center.dashboard(outsider)["history"] == []
    reader = InteractionScope("tenant-a", "workspace-a", "x")
    with pytest.raises(PermissionError, match="write"):
        center.create_project(
            InteractionProject("x", "x", "", "tenant-a", "workspace-a", "x"), reader
        )


def test_api_contract(center):
    from tiktok.interaction_center.api import ROUTES, register_interaction_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, **kwargs):
            self.routes.append((path, endpoint, kwargs))

    app = App()
    register_interaction_routes(app, center)
    paths = {item[0] for item in app.routes}
    assert set(ROUTES) <= paths
    assert {"/tiktok/interaction/dashboard", "/tiktok/interaction/metrics"} <= paths


def test_no_prohibited_social_or_bypass_modules():
    from pathlib import Path

    root = Path(__file__).parents[2] / "tiktok" / "interaction_center"
    prohibited = {"telegram", "whatsapp", "facebook", "instagram", "discord"}
    assert not (prohibited & {path.name.casefold() for path in root.iterdir()})
