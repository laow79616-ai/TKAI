from __future__ import annotations

import pytest

from collaboration import (
    CollaborationScope,
    EnterpriseAICollaborationPlatform,
    HandoffType,
    PresenceStatus,
)
from collaboration.api import register_collaboration_routes
from collaboration.dashboard import SECTIONS

PERMISSIONS = {
    "collaboration:admin",
    "collaboration:read",
    "collaboration:write",
    "collaboration:message",
    "collaboration:memory:read",
    "collaboration:memory:write",
    "collaboration:task",
    "collaboration:handoff",
}


def configured() -> tuple[EnterpriseAICollaborationPlatform, CollaborationScope]:
    platform = EnterpriseAICollaborationPlatform()
    scope = CollaborationScope("tenant-a", "workspace-a", "alice")
    platform.security.grant(scope, PERMISSIONS)
    platform.create_workspace(
        {
            "organization": "organization-a",
            "name": "AI Operations",
            "description": "Human and agent operations",
            "members": ["alice", "support-agent"],
            "roles": {"alice": "owner", "support-agent": "agent"},
            "metadata": {"region": "cn"},
        },
        scope,
    )
    return platform, scope


def test_workspace_project_session_and_dashboard() -> None:
    platform, scope = configured()
    project = platform.create_project(
        {
            "id": "project-1",
            "owner": "alice",
            "applications": ["support"],
            "agents": ["support-agent"],
            "knowledge": ["support-kb"],
            "workflow": "triage",
            "status": "active",
            "version": "3.2.0",
        },
        scope,
    )
    session = platform.create_session(
        {
            "id": "session-1",
            "participants": ["alice"],
            "agent_participants": ["support-agent"],
            "shared_context": {
                "variables": {"case": "42"},
                "artifacts": [{"id": "log"}],
                "knowledge_references": ["support-kb"],
                "application_state": {"view": "case"},
                "workflow_state": {"step": "triage"},
            },
        },
        scope,
    )
    assert project.version == "3.2.0"
    assert session.shared_context.variables["case"] == "42"
    assert set(SECTIONS) <= set(platform.dashboard(scope)["sections"])


@pytest.mark.parametrize("status", [item.value for item in PresenceStatus])
def test_presence_supports_humans_and_agents(status: str) -> None:
    platform, scope = configured()
    assert platform.set_presence("support-agent", status, scope).value == status


def test_threads_mentions_replies_attachments_and_notifications() -> None:
    platform, scope = configured()
    platform.create_session({"id": "session-1"}, scope)
    first = platform.send_message(
        {
            "id": "message-1",
            "session_id": "session-1",
            "thread_id": "thread-1",
            "body": "Please review",
            "mentions": ["bob"],
            "attachments": [{"name": "case.txt", "url": "artifact://case"}],
        },
        scope,
    )
    reply = platform.send_message(
        {
            "session_id": "session-1",
            "thread_id": first.thread_id,
            "reply_to": first.id,
            "body": "Reviewed",
        },
        scope,
    )
    assert reply.reply_to == first.id
    assert len(platform.notifications) == 1


def test_shared_context_memory_retention_namespace_and_isolation() -> None:
    platform, scope = configured()
    platform.create_session({"id": "session-1"}, scope)
    updated = platform.update_context(
        "session-1",
        {
            "variables": {"approved": True},
            "knowledge_references": ["policy"],
            "workflow_state": {"approved": True},
        },
        scope,
    )
    platform.write_memory("session-1:retention-30d", "decision", "approved", scope)
    assert updated.variables["approved"] is True
    assert (
        platform.read_memory("session-1:retention-30d", "decision", scope) == "approved"
    )
    other = CollaborationScope("tenant-b", "workspace-a", "alice")
    platform.security.grant(other, PERMISSIONS)
    with pytest.raises(PermissionError, match="Cross-tenant"):
        platform._get(platform.sessions, "session-1", other)


def test_tasks_dependencies_handoffs_timeline_audit_and_metrics() -> None:
    platform, scope = configured()
    first = platform.create_task(
        {
            "id": "investigate",
            "title": "Investigate",
            "assignment": "support-agent",
            "priority": "high",
            "due_date": "2026-08-01",
        },
        scope,
    )
    second = platform.create_task(
        {
            "id": "approve",
            "title": "Approve",
            "dependencies": [first.id],
        },
        scope,
    )
    updated = platform.update_task(second.id, {"status": "in_progress"}, scope)
    assert updated.status.value == "in_progress"
    for handoff_type in HandoffType:
        platform.handoff(
            {
                "source": "alice",
                "target": "support-agent",
                "type": handoff_type.value,
                "context": {"task": first.id},
            },
            scope,
        )
    metrics = platform.metrics.snapshot()
    assert metrics["tasks_total"] == 2
    assert metrics["handoffs_total"] == 4
    assert platform.timeline_for(scope)
    assert platform.security.audit


def test_rbac_workspace_isolation_and_permission_validation() -> None:
    platform, scope = configured()
    platform.create_project({"id": "project-1"}, scope)
    unprivileged = CollaborationScope("tenant-a", "workspace-a", "bob")
    with pytest.raises(PermissionError, match="collaboration:write"):
        platform.create_project({"id": "project-2"}, unprivileged)
    other_workspace = CollaborationScope("tenant-a", "workspace-b", "alice")
    platform.security.grant(other_workspace, PERMISSIONS)
    with pytest.raises(PermissionError, match="Cross-workspace"):
        platform._get(platform.projects, "project-1", other_workspace)


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_and_metrics_contract() -> None:
    app = App()
    platform, _ = configured()
    register_collaboration_routes(app, platform)
    for path in (
        "/workspaces",
        "/projects",
        "/collaboration",
        "/tasks",
        "/timeline",
        "/notifications",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    for metric in (
        "workspaces_total",
        "projects_total",
        "collaboration_sessions_total",
        "tasks_total",
        "handoffs_total",
        "messages_total",
        "notifications_total",
    ):
        assert metric in platform.metrics.render_prometheus()
