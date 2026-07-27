from datetime import timedelta

import pytest

from automation_platform import (
    METRICS,
    Action,
    ActionType,
    Automation,
    AutomationPlatform,
    AutomationScope,
    AutomationStatus,
    Condition,
    ConditionType,
    ExecutionStatus,
    Pipeline,
    RollbackPlan,
    Schedule,
    Trigger,
    TriggerType,
    utcnow,
)
from automation_platform.dashboard import SECTIONS


@pytest.fixture
def configured() -> tuple[AutomationPlatform, AutomationScope]:
    platform = AutomationPlatform()
    scope = AutomationScope(
        "tenant-a",
        "workspace-a",
        "builder",
        frozenset(
            {
                "automation:read",
                "automation:write",
                "automation:execute",
                "automation:approve",
            }
        ),
    )
    platform.create_automation(
        Automation(
            "auto-a",
            "Incident response",
            "Diagnose and remediate",
            "platform",
            scope.tenant,
            scope.workspace,
            "operations",
        ),
        scope,
    )
    return platform, scope


def test_lifecycle_isolation_rbac_audit_and_metrics(
    configured: tuple[AutomationPlatform, AutomationScope],
) -> None:
    platform, scope = configured
    foreign = AutomationScope("tenant-b", "workspace-a", "viewer")
    assert platform.list_automations(scope)[0].owner == "platform"
    assert platform.list_automations(foreign) == []
    with pytest.raises(PermissionError, match="RBAC"):
        platform.create_automation(
            Automation("x", "X", "X", "x", "tenant-b", "workspace-a", "x"),
            foreign,
        )
    platform.set_status("auto-a", AutomationStatus.ENABLED, scope)
    platform.set_status("auto-a", AutomationStatus.PAUSED, scope)
    with pytest.raises(ValueError, match="Invalid lifecycle"):
        platform.set_status("auto-a", AutomationStatus.DELETED, scope)
    assert platform.metrics.snapshot()["automation_total"] == 1
    assert platform.audit[0].action == "automation.create"


def test_triggers_conditions_scheduler_and_secrets(
    configured: tuple[AutomationPlatform, AutomationScope],
) -> None:
    platform, scope = configured
    for kind in TriggerType:
        platform.add_trigger(
            Trigger(
                f"trigger-{kind.value}",
                "auto-a",
                kind,
                scope.tenant,
                scope.workspace,
                secret_references=("secret://automation/token",),
            ),
            scope,
        )
    with pytest.raises(ValueError, match="Secrets"):
        platform.add_action(
            Action(
                "bad",
                "Bad",
                ActionType.CONNECTOR,
                scope.tenant,
                scope.workspace,
                secret_references=("plaintext",),
            ),
            scope,
        )
    context = {"ready": True, "score": 90}
    values = (
        Condition("boolean", ConditionType.BOOLEAN, "ready"),
        Condition("threshold", ConditionType.THRESHOLD, "score", "gte", 80),
    )
    assert all(value.evaluate(context) for value in values)
    schedule = platform.add_schedule(
        Schedule(
            "schedule-a",
            "auto-a",
            scope.tenant,
            scope.workspace,
            "cron",
            "* * * * *",
            "Asia/Shanghai",
            next_run_at=utcnow() - timedelta(minutes=1),
        ),
        scope,
    )
    assert platform.due_schedules(scope) == [schedule]


def test_retry_rollback_checkpoint_history_dashboard(
    configured: tuple[AutomationPlatform, AutomationScope],
) -> None:
    platform, scope = configured
    first = Action(
        "first", "Workflow", ActionType.WORKFLOW, scope.tenant, scope.workspace
    )
    second = Action("second", "Agent", ActionType.AGENT, scope.tenant, scope.workspace)
    platform.add_action(first, scope)
    platform.add_action(second, scope)
    pipeline = platform.add_pipeline(
        Pipeline(
            "pipeline-a",
            "Response",
            scope.tenant,
            scope.workspace,
            ("first", "second"),
            retry_limit=1,
            checkpoint=True,
        ),
        scope,
    )
    platform.bind_pipeline("auto-a", pipeline.id, scope)
    platform.add_rollback_plan(
        RollbackPlan(
            "rollback-a",
            pipeline.id,
            scope.tenant,
            scope.workspace,
            {"first": "undo-first"},
        ),
        scope,
    )

    def handler(action: Action, context: object) -> object:
        if action.id == "second":
            raise RuntimeError("agent unavailable")
        return {"ok": True}

    platform.register_handler(ActionType.WORKFLOW, handler)
    platform.register_handler(ActionType.AGENT, handler)
    platform.set_status("auto-a", AutomationStatus.ENABLED, scope)
    execution = platform.run("auto-a", {}, scope)
    assert execution.status is ExecutionStatus.ROLLED_BACK
    assert execution.results["rollback"]["checkpoint_restored"]
    assert platform.metrics.snapshot()["automation_retries_total"] == 1
    assert platform.history(scope) == [execution]
    dashboard = platform.dashboard(scope)
    assert set(SECTIONS) == set(dashboard)
    assert set(dashboard["metrics"]) == set(METRICS)


def test_approval_integration(
    configured: tuple[AutomationPlatform, AutomationScope],
) -> None:
    platform, scope = configured
    action = Action(
        "deploy",
        "Deploy",
        ActionType.APPLICATION,
        scope.tenant,
        scope.workspace,
        requires_approval=True,
    )
    platform.add_action(action, scope)
    platform.add_pipeline(
        Pipeline("pipeline-a", "Deploy", scope.tenant, scope.workspace, (action.id,)),
        scope,
    )
    platform.bind_pipeline("auto-a", "pipeline-a", scope)
    platform.set_status("auto-a", AutomationStatus.ENABLED, scope)
    assert platform.run("auto-a", {}, scope).status is ExecutionStatus.WAITING_APPROVAL
    approval = platform.request_approval("auto-a", scope)
    platform.decide_approval(approval.id, True, scope)
    assert (
        platform.run("auto-a", {}, scope, approval.id).status
        is ExecutionStatus.SUCCEEDED
    )
