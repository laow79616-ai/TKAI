from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.workflow_center import (
    Approval,
    ApprovalKind,
    ApprovalStatus,
    ConditionKind,
    ExecutionStatus,
    NodeKind,
    ScheduleKind,
    TikTokWorkflowOrchestrationCenter,
    Workflow,
    WorkflowCondition,
    WorkflowEdge,
    WorkflowExecution,
    WorkflowNode,
    WorkflowSchedule,
    WorkflowScope,
    WorkflowStatus,
    WorkflowTemplate,
    WorkflowVariable,
)
from tiktok.workflow_center.api import ROUTES, register_workflow_center_routes
from tiktok.workflow_center.metrics import METRIC_NAMES
from tiktok.workflow_center.models import utcnow


class Port:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.calls: list[tuple[str, str]] = []

    def execute(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> dict[str, Any]:
        self.calls.append(("execute", action))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("mock failure")
        return {"result": "ok", "action": action}

    def rollback(
        self, action: str, payload: dict[str, Any], scope: WorkflowScope
    ) -> None:
        self.calls.append(("rollback", action))


def scope(workspace: str = "w1") -> WorkflowScope:
    return WorkflowScope(
        "tenant-1",
        workspace,
        "operator",
        frozenset({"tiktok:workflow:admin"}),
    )


def workflow(
    *,
    status: WorkflowStatus = WorkflowStatus.DRAFT,
    nodes: list[WorkflowNode] | None = None,
) -> Workflow:
    return Workflow(
        "wf-1",
        "Publish approved content",
        "Orchestrates existing centers",
        "tenant-1",
        "w1",
        "owner",
        status=status,
        nodes=nodes or [WorkflowNode("n1", NodeKind.CONTENT_CENTER, "prepare")],
    )


def approve(
    center: TikTokWorkflowOrchestrationCenter,
    kind: ApprovalKind,
    resource: str,
    request_scope: WorkflowScope,
) -> Approval:
    item = center.request_approval(
        Approval(
            f"approval-{kind.value}-{resource}",
            "tenant-1",
            "w1",
            kind,
            resource,
            "reviewer",
            utcnow() + timedelta(hours=1),
        ),
        request_scope,
    )
    return center.decide_approval(
        item.id, ApprovalStatus.APPROVED, "approved test fixture", request_scope
    )


def ready_center(
    ports: dict[NodeKind, Port] | None = None,
    nodes: list[WorkflowNode] | None = None,
) -> tuple[TikTokWorkflowOrchestrationCenter, WorkflowScope, Workflow]:
    center = TikTokWorkflowOrchestrationCenter(ports)
    request_scope = scope()
    item = center.create_workflow(workflow(nodes=nodes), request_scope)
    center.transition_workflow(item.id, WorkflowStatus.REVIEW, request_scope)
    approve(center, ApprovalKind.WORKFLOW, item.id, request_scope)
    center.transition_workflow(item.id, WorkflowStatus.APPROVED, request_scope)
    center.transition_workflow(item.id, WorkflowStatus.READY, request_scope)
    return center, request_scope, item


def test_workflow_crud_lifecycle_rbac_isolation_and_validation() -> None:
    center = TikTokWorkflowOrchestrationCenter()
    request_scope = scope()
    item = center.create_workflow(workflow(), request_scope)
    updated = center.update_workflow(item.id, request_scope, name="Updated")
    assert updated.name == "Updated" and updated.version == 2
    assert center.list_workflows(scope("other")) == []
    with pytest.raises(PermissionError):
        center.transition_workflow(item.id, WorkflowStatus.REVIEW, scope("other"))
    with pytest.raises(ValueError):
        center.create_workflow(
            Workflow(
                "bad",
                "Bad",
                "",
                "tenant-1",
                "w1",
                "owner",
                metadata={"token": "plaintext"},
            ),
            request_scope,
        )
    center.transition_workflow(item.id, WorkflowStatus.REVIEW, request_scope)
    with pytest.raises(PermissionError):
        center.transition_workflow(item.id, WorkflowStatus.APPROVED, request_scope)


def test_templates_conditions_variables_and_graph_validation() -> None:
    center = TikTokWorkflowOrchestrationCenter()
    request_scope = scope()
    node = WorkflowNode("n1", NodeKind.ACCOUNT_CENTER, "health")
    center.create_template(
        WorkflowTemplate("template-1", "tenant-1", "w1", "Health", "", [node]),
        request_scope,
    )
    condition = WorkflowCondition(
        "condition-1", ConditionKind.RISK_SCORE, "risk_score", "lte", 40
    )
    assert condition.evaluate({"risk_score": 25})
    with pytest.raises(ValueError):
        WorkflowVariable("required", required=True).validate()
    WorkflowVariable(
        "credential", encrypted_reference="secret://vault/tiktok"
    ).validate()
    invalid = workflow(nodes=[node])
    invalid.edges = [WorkflowEdge("missing", "n1")]
    with pytest.raises(ValueError):
        invalid.validate()


def test_execution_priority_retry_checkpoint_history_analytics_and_rollback() -> None:
    port = Port(failures=1)
    node = WorkflowNode("n1", NodeKind.CONTENT_CENTER, "prepare", maximum_retries=1)
    center, request_scope, item = ready_center({NodeKind.CONTENT_CENTER: port}, [node])
    execution = WorkflowExecution(
        "exec-1", "tenant-1", "w1", item.id, item.version, "operator", priority=90
    )
    approve(center, ApprovalKind.EXECUTION, execution.id, request_scope)
    center.enqueue_execution(execution, request_scope)
    result = center.execute_next(request_scope)
    assert result is not None
    assert result.status is ExecutionStatus.COMPLETED
    assert result.retry_count == 1 and result.checkpoint == 1
    assert center.analytics(request_scope)["success_rate"] == 1
    assert center.history
    center.rollback(execution.id, request_scope)
    assert execution.status is ExecutionStatus.ROLLED_BACK
    assert ("rollback", "prepare") in port.calls


def test_high_risk_approval_enforcement_and_expiration() -> None:
    node = WorkflowNode("n1", NodeKind.PUBLISHING_CENTER, "publish", high_risk=True)
    center, request_scope, item = ready_center(nodes=[node])
    execution = WorkflowExecution(
        "exec-1", "tenant-1", "w1", item.id, item.version, "operator"
    )
    approve(center, ApprovalKind.EXECUTION, execution.id, request_scope)
    center.enqueue_execution(execution, request_scope)
    failed = center.execute_next(request_scope)
    assert failed is not None and failed.status is ExecutionStatus.FAILED
    approve(
        center,
        ApprovalKind.HIGH_RISK_STEP,
        f"{execution.id}:{node.id}",
        request_scope,
    )
    resumed = center.resume(execution.id, request_scope)
    assert resumed.status is ExecutionStatus.COMPLETED
    expired = center.request_approval(
        Approval(
            "expired",
            "tenant-1",
            "w1",
            ApprovalKind.EXECUTION,
            "exec-2",
            "reviewer",
            utcnow() + timedelta(microseconds=1),
        ),
        request_scope,
    )
    expired.expires_at = utcnow() - timedelta(seconds=1)
    assert center.expire_approvals(request_scope) == 1


def test_scheduling_queues_cancellation_and_dashboard() -> None:
    center, request_scope, item = ready_center()
    schedule = center.create_schedule(
        WorkflowSchedule(
            "schedule-1",
            "tenant-1",
            "w1",
            item.id,
            ScheduleKind.RECURRING,
            "Asia/Shanghai",
            "0 * * * *",
            (8, 22),
            3,
        ),
        request_scope,
    )
    assert schedule.maximum_concurrent_executions == 3
    execution = WorkflowExecution(
        "exec-1", "tenant-1", "w1", item.id, item.version, "operator"
    )
    approve(center, ApprovalKind.EXECUTION, execution.id, request_scope)
    center.enqueue_execution(execution, request_scope)
    assert center.queue_metrics(request_scope)["execution_queue"] == 1
    center.cancel(execution.id, request_scope)
    assert execution.status is ExecutionStatus.CANCELLED
    dashboard = center.dashboard(request_scope)
    assert "Workflow Designer" in dashboard["sections"]
    assert "Statistics" in dashboard["sections"]


def test_api_routes_and_metrics_contract() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    center = TikTokWorkflowOrchestrationCenter()
    register_workflow_center_routes(app, center)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/workflows/dashboard" in app.routes
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_only_approved_tiktok_node_kinds_are_exposed() -> None:
    assert {kind.value for kind in NodeKind} == {
        "account_center",
        "browser_runtime",
        "proxy_center",
        "ai_account_farming",
        "content_center",
        "publishing_center",
        "data_collection_center",
        "interaction_center",
        "risk_control_center",
        "manual_approval",
        "delay",
        "condition",
        "notification",
    }
