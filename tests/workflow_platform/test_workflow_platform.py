from datetime import datetime, timedelta, timezone

import pytest

from workflow_platform import Node, NodeType, Scope, WorkflowPlatform, WorkflowStatus
from workflow_platform.approval import Approval
from workflow_platform.conditions import evaluate, switch
from workflow_platform.connectors import BoundedConnector, ConnectorRequest
from workflow_platform.dashboard import SECTIONS, dashboard
from workflow_platform.designer import Designer
from workflow_platform.execution import ExecutionOptions
from workflow_platform.forms import Form
from workflow_platform.security import SecurityPolicy
from workflow_platform.variables import Variables


def payload(workflow_id: str = "wf-1") -> dict[str, object]:
    return {
        "id": workflow_id,
        "name": "Enterprise onboarding",
        "description": "Validated workflow",
        "owner": "alice",
        "tenant": "tenant-a",
        "workspace": "workspace-a",
        "category": "operations",
        "tags": ["enterprise"],
        "nodes": [
            {"id": "start", "type": "start"},
            {"id": "end", "type": "end"},
        ],
        "edges": [{"source": "start", "target": "end"}],
    }


def test_lifecycle_designer_versions_undo_redo_and_isolation() -> None:
    platform = WorkflowPlatform()
    item = platform.create(payload())
    assert item.status is WorkflowStatus.DRAFT
    assert platform.publish(item.id, item.scope).status is WorkflowStatus.PUBLISHED
    with pytest.raises(PermissionError):
        platform.get(item.id, Scope("tenant-b", "workspace-a"))

    designer = Designer(item)
    updated = designer.update(
        nodes=item.nodes + (Node("model", NodeType.MODEL),), edges=item.edges
    )
    assert updated.version == 2
    assert designer.undo().version == 1
    assert designer.redo().version == 2


def test_execution_retry_checkpoint_resume_rollback_cancel_and_metrics() -> None:
    platform = WorkflowPlatform()
    workflow = platform.create(payload())
    platform.publish(workflow.id, workflow.scope)
    calls = 0

    def handler(node: Node, variables: Variables) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("retry")
        return node.id

    platform.engine.register(NodeType.START, handler)
    result = platform.run(
        workflow.id,
        workflow.scope,
        {"name": "TKAI"},
        ExecutionOptions(retries=1),
    )
    assert result.status is WorkflowStatus.COMPLETED
    assert result.checkpoint == 2
    assert result.attempts == 1
    assert platform.metrics.snapshot()["workflow_success_total"] == 1
    assert platform.engine.rollback(result.id, 1).checkpoint == 1

    resumed = platform.engine.run(
        workflow, {}, execution_id="resume", resume_from=1
    )
    assert resumed.checkpoint == 2
    platform.engine.cancel("cancelled")
    cancelled = platform.engine.run(workflow, {}, execution_id="cancelled")
    assert cancelled.status is WorkflowStatus.FAILED


def test_variables_conditions_forms_approvals_connectors_security_dashboard() -> None:
    variables = Variables(
        inputs={"name": "TKAI"}, secrets={"key": "never returned"}
    )
    assert variables.resolve("${input.name}") == "TKAI"
    assert variables.resolve("${secret.key}") == {"secret_reference": "key"}
    assert evaluate("regex", "TKAI-31", r"TKAI-\d+")
    assert evaluate("greater", 3, 2)
    assert switch("a", {"a": "first"}, "default") == "first"

    form = Form(
        "form-1",
        {
            "required": ["name"],
            "properties": {"name": {"type": "string"}},
        },
        {"name": "default"},
        attachments=True,
    )
    assert form.validate({})["name"] == "default"

    approval = Approval("approval-1", "run-1", ("alice",), timeout_seconds=1)
    approval.decide("alice", "approved")
    assert approval.audit[-1]["decision"] == "approved"
    approval.created_at = datetime.now(timezone.utc) - timedelta(seconds=2)
    assert approval.timed_out()

    connector = BoundedConnector("database", {"query": [{"id": 1}]})
    response = connector.execute(ConnectorRequest("query", {}, limit=1))
    assert response["bounded"] is True

    security = SecurityPolicy()
    scope = Scope("tenant-a", "workspace-a")
    security.grant("alice", scope, {"run"})
    security.require("alice", scope, "run")
    with pytest.raises(PermissionError):
        security.require("bob", scope, "run")

    platform = WorkflowPlatform()
    platform.create(payload())
    view = dashboard(platform, scope)
    assert set(SECTIONS) <= set(view["sections"])
    assert view["metrics"]["workflow_total"] == 1


def test_validation_templates_and_limits() -> None:
    platform = WorkflowPlatform(execution_limit=1)
    item = platform.create(payload())
    platform.templates.add(item)
    assert platform.templates.search("onboarding", "operations") == (item,)
    clone = platform.templates.clone("wf-1", "wf-2", item.scope, "bob")
    assert clone.owner == "bob"
    assert platform.templates.export("wf-1")["id"] == "wf-1"
    with pytest.raises(ValueError):
        ConnectorRequest("query", {}, limit=1001)
