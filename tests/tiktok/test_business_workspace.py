"""Offline coverage for the Enterprise TikTok Business Workspace."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tiktok.business_workspace import (
    ApprovalKind,
    ApprovalStatus,
    BuiltinRole,
    BusinessApproval,
    BusinessOperation,
    BusinessProject,
    BusinessScope,
    BusinessWorkspace,
    CalendarEntry,
    CalendarKind,
    CoordinationRequest,
    CoordinationTarget,
    LifecycleStatus,
    Member,
    OperationKind,
    Permission,
    Role,
    TikTokBusinessWorkspace,
)
from tiktok.business_workspace.adapters import NullCoordinationPort
from tiktok.business_workspace.api import ROUTES, register_business_workspace_routes
from tiktok.business_workspace.metrics import METRIC_NAMES
from tiktok.business_workspace.models import utcnow


def scope(workspace: str = "default") -> BusinessScope:
    return BusinessScope(
        "default",
        workspace,
        "operator",
        frozenset({"tiktok:business:admin"}),
    )


def workspace() -> BusinessWorkspace:
    return BusinessWorkspace(
        "workspace-1",
        "Launch business",
        "Unified launch operations",
        "default",
        "operator",
        "default",
    )


def project() -> BusinessProject:
    return BusinessProject(
        "project-1",
        "workspace-1",
        "Launch",
        "default",
        "default",
        "operator",
        campaign_reference="ref://campaign/launch",
        creator_workspace_reference="ref://creator/project-1",
        content_pipeline_reference="ref://pipeline/launch",
        publishing_plan_reference="ref://publishing/launch",
        workflow_reference="ref://workflow/launch",
        automation_reference="ref://automation/launch",
        execution_reference="ref://execution/launch",
    )


def ready_center(
    coordinator: NullCoordinationPort | None = None,
) -> TikTokBusinessWorkspace:
    ports = (
        {CoordinationTarget.EXECUTION_ENGINE: coordinator}
        if coordinator is not None
        else None
    )
    center = TikTokBusinessWorkspace(coordinators=ports)
    center.create_workspace(workspace(), scope())
    center.create_project(project(), scope())
    return center


def approve(
    center: TikTokBusinessWorkspace, reference: str = "ref://business/project-1"
) -> BusinessApproval:
    return center.decide_approval(
        BusinessApproval(
            "approval-1",
            reference,
            "default",
            "default",
            ApprovalKind.PROJECT,
            "reviewer",
            ApprovalStatus.APPROVED,
            utcnow() + timedelta(hours=1),
        ),
        scope(),
    )


def test_workspace_crud_projects_and_lifecycle_approval() -> None:
    center = ready_center()
    updated = center.update_workspace(
        "workspace-1", {"description": "Updated"}, scope()
    )
    assert updated.version == 2
    center.transition("project-1", LifecycleStatus.PLANNING, scope())
    center.transition("project-1", LifecycleStatus.REVIEW, scope())
    with pytest.raises(PermissionError, match="approval"):
        center.transition("project-1", LifecycleStatus.APPROVED, scope())
    approve(center)
    approved = center.transition("project-1", LifecycleStatus.APPROVED, scope())
    assert approved.status is LifecycleStatus.APPROVED
    assert center.metrics.values["tiktok_business_campaigns_total"] == 1
    deleted = center.delete_workspace("workspace-1", scope())
    assert deleted.status is LifecycleStatus.DELETED


def test_operations_calendar_and_timezone_validation() -> None:
    center = ready_center()
    operation = center.create_operation(
        BusinessOperation(
            "operation-1",
            "project-1",
            "default",
            "default",
            OperationKind.RESOURCE_COORDINATION,
            "operator",
            resource_references=["ref://resource/browser-1"],
        ),
        scope(),
    )
    entry = center.add_calendar_entry(
        CalendarEntry(
            "calendar-1",
            "project-1",
            "default",
            "default",
            CalendarKind.CAMPAIGN,
            "Launch",
            utcnow() + timedelta(days=1),
            "Asia/Shanghai",
            30,
        ),
        scope(),
    )
    assert operation.kind is OperationKind.RESOURCE_COORDINATION
    assert entry.timezone_name == "Asia/Shanghai"
    entry.timezone_name = "not a timezone!"
    with pytest.raises(ValueError, match="Timezone"):
        entry.validate()


def test_roles_permissions_members_and_isolation() -> None:
    center = ready_center()
    role = center.add_role(
        Role(
            "analyst-role",
            "Analyst",
            "default",
            "default",
            frozenset(
                {Permission.WORKSPACE_ACCESS, Permission.ANALYTICS_ACCESS}
            ),
            BuiltinRole.ANALYST,
        ),
        scope(),
    )
    member = center.add_member(
        Member(
            "member-1",
            "workspace-1",
            "default",
            "default",
            "Analyst",
            role.id,
        ),
        scope(),
    )
    assert center.authorize_member(
        member.id, Permission.ANALYTICS_ACCESS, scope()
    )
    assert not center.authorize_member(
        member.id, Permission.APPROVAL_ACCESS, scope()
    )
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_workspace(workspace(), scope("other"))
    reader = BusinessScope("default", "default", "reader")
    with pytest.raises(PermissionError, match="write"):
        center.create_workspace(workspace(), reader)


def test_metadata_reference_and_role_validation() -> None:
    center = TikTokBusinessWorkspace()
    unsafe = workspace()
    unsafe.metadata = {"token": "never-log"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create_workspace(unsafe, scope())
    invalid = project()
    invalid.workflow_reference = "https://not-opaque"
    center.create_workspace(workspace(), scope())
    with pytest.raises(ValueError, match="opaque"):
        center.create_project(invalid, scope())
    empty_role = Role(
        "empty", "Empty", "default", "default", frozenset()
    )
    with pytest.raises(ValueError, match="permission"):
        center.add_role(empty_role, scope())


def test_approval_expiration_and_rejection_audit() -> None:
    center = ready_center()
    expired = BusinessApproval(
        "expired",
        "ref://business/project-1",
        "default",
        "default",
        ApprovalKind.OPERATIONAL,
        "reviewer",
        ApprovalStatus.APPROVED,
        utcnow() - timedelta(seconds=1),
    )
    with pytest.raises(ValueError, match="past expiration"):
        center.decide_approval(expired, scope())
    rejected = BusinessApproval(
        "rejected",
        "ref://business/project-1",
        "default",
        "default",
        ApprovalKind.OPERATIONAL,
        "reviewer",
        ApprovalStatus.REJECTED,
        notes="Needs revision",
    )
    center.decide_approval(rejected, scope())
    assert center.audit[-1]["action"] == "approval.rejected"


def test_coordination_is_proposal_only_and_approval_gated() -> None:
    port = NullCoordinationPort()
    center = ready_center(port)
    request = CoordinationRequest(
        "coordination-1",
        "project-1",
        "default",
        "default",
        CoordinationTarget.EXECUTION_ENGINE,
        "ref://execution/launch",
        "ref://business/project-1",
    )
    with pytest.raises(PermissionError, match="approval"):
        center.coordinate(request, scope())
    approve(center)
    receipt = center.coordinate(request, scope())
    assert receipt.startswith("ref://business-coordination/")
    assert port.proposals[0]["target"] == "execution_engine"
    request.proposal_only = False
    with pytest.raises(ValueError, match="proposal-only"):
        request.validate()


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert callable(endpoint)
        assert tags == ["tiktok-business-workspace"]
        self.routes.append((path, tuple(methods)))


def test_api_dashboard_analytics_history_metrics_and_openapi_contracts() -> None:
    center = ready_center()
    app = FakeApp()
    register_business_workspace_routes(app, center)
    paths = {path for path, _ in app.routes}
    assert set(ROUTES).issubset(paths)
    assert "/tiktok/business-workspace/dashboard" in paths
    assert "/tiktok/business-workspace/history" in paths
    assert "/tiktok/business-workspace/metrics" in paths
    assert len(center.dashboard(scope())["sections"]) == 9
    assert center.analytics(scope())["project_kpis"]["total"] == 1
    assert center.history(scope())["audit_trail"]
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
