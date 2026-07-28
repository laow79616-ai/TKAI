from __future__ import annotations

from typing import Any

import pytest

from tiktok.automation_engine import (
    APPROVED_MODULES,
    Automation,
    AutomationApproval,
    AutomationCondition,
    AutomationExecution,
    AutomationPlan,
    AutomationScope,
    AutomationStatus,
    AutomationTemplate,
    AutomationTrigger,
    ConditionKind,
    ExecutionStatus,
    ExecutionStep,
    QueueKind,
    TikTokAutomationEngine,
    TriggerKind,
)
from tiktok.automation_engine.api import ROUTES, register_automation_routes
from tiktok.automation_engine.metrics import METRIC_NAMES


class Port:
    def __init__(self, failures: int = 0, restricted: bool = False) -> None:
        self.failures = failures
        self.restricted = restricted
        self.calls: list[tuple[str, str]] = []

    def health(self, module: str, scope: AutomationScope) -> dict[str, Any]:
        return {"healthy": True, "restriction_unresolved": self.restricted}

    def execute(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> dict[str, Any]:
        self.calls.append((module, action))
        if self.failures:
            self.failures -= 1
            raise RuntimeError("mock failure")
        return {"ok": True}

    def rollback(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> None:
        self.calls.append((module, action))


def scope(workspace: str = "local") -> AutomationScope:
    return AutomationScope(
        "single-user",
        workspace,
        "operator",
        frozenset({"tiktok:automation:admin"}),
    )


def ready_engine(
    port: Port | None = None,
    *,
    attempts: int = 3,
) -> tuple[TikTokAutomationEngine, AutomationScope, Automation, AutomationPlan]:
    engine = TikTokAutomationEngine(port)
    request_scope = scope()
    plan = engine.create_plan(
        AutomationPlan(
            "plan-1",
            "single-user",
            "local",
            "Bounded publishing",
            "workflow-1",
            maximum_attempts=attempts,
        ),
        request_scope,
    )
    item = engine.create_automation(
        Automation(
            "automation-1",
            "Approved local flow",
            "Safe orchestration",
            "single-user",
            "local",
            "operator",
            plan_reference=plan.id,
        ),
        request_scope,
    )
    engine.transition(item.id, AutomationStatus.REVIEW, request_scope)
    engine.approve(
        AutomationApproval("approval-1", "single-user", "local", item.id, "operator"),
        request_scope,
    )
    engine.transition(item.id, AutomationStatus.APPROVED, request_scope)
    engine.transition(item.id, AutomationStatus.READY, request_scope)
    return engine, request_scope, item, plan


def execution(item: Automation, plan: AutomationPlan) -> AutomationExecution:
    return AutomationExecution(
        "execution-1",
        "single-user",
        "local",
        item.id,
        plan.id,
        "operator",
        [
            ExecutionStep(
                "step-1",
                "publishing_center",
                "publish-approved",
                rollback_action="withdraw",
            )
        ],
        priority=90,
    )


def test_lifecycle_plan_template_rbac_isolation_and_secret_validation() -> None:
    engine, request_scope, item, plan = ready_engine()
    assert item.status is AutomationStatus.READY
    assert engine.list_automations(scope("other")) == []
    with pytest.raises(PermissionError):
        engine.update_automation(item.id, scope("other"), name="cross-scope")
    with pytest.raises(ValueError):
        Automation(
            "bad",
            "bad",
            "",
            "single-user",
            "local",
            "operator",
            metadata={"token": "plaintext"},
        ).validate()
    template = engine.create_template(
        AutomationTemplate("template-1", "single-user", "local", "Reusable", plan.id),
        request_scope,
    )
    assert template.plan_reference == plan.id and plan.reusable


def test_triggers_and_all_condition_kinds() -> None:
    engine, request_scope, item, _ = ready_engine()
    for kind in TriggerKind:
        config = (
            {"interface": "automation-trigger://local/test"}
            if kind is TriggerKind.CUSTOM
            else {}
        )
        engine.create_trigger(
            AutomationTrigger(
                f"trigger-{kind.value}",
                "single-user",
                "local",
                item.id,
                kind,
                config,
            ),
            request_scope,
        )
    assert len(engine.triggers) == len(TriggerKind)
    with pytest.raises(ValueError):
        AutomationTrigger(
            "bad", "single-user", "local", item.id, TriggerKind.CUSTOM
        ).validate()
    for kind in ConditionKind:
        condition = engine.create_condition(
            AutomationCondition(
                f"condition-{kind.value}",
                "single-user",
                "local",
                kind,
                kind.value,
                "eq",
                True,
            ),
            request_scope,
        )
        assert condition.evaluate({kind.value: True})


def test_priority_execution_retry_checkpoint_rollback_monitoring_and_analytics() -> (
    None
):
    port = Port(failures=1)
    engine, request_scope, item, plan = ready_engine(port)
    run = execution(item, plan)
    engine.enqueue(run, request_scope)
    assert engine.queue_health(request_scope)["priority"] == 1
    result = engine.execute_next(request_scope)
    assert result is run and result.status is ExecutionStatus.COMPLETED
    assert result.retry_count == 1 and result.checkpoint == 1
    assert engine.analytics(request_scope)["success_rate"] == 1
    assert engine.monitoring(request_scope)["execution_health"] == "healthy"
    engine.rollback(run.id, request_scope)
    assert run.status is ExecutionStatus.ROLLED_BACK
    assert ("publishing_center", "withdraw") in port.calls


def test_failure_recovery_limits_and_restriction_safe_stop() -> None:
    failing = Port(failures=3)
    engine, request_scope, item, plan = ready_engine(failing, attempts=2)
    run = execution(item, plan)
    engine.enqueue(run, request_scope, QueueKind.EXECUTION)
    assert engine.execute_next(request_scope).status is ExecutionStatus.FAILED
    engine.recover(run.id, request_scope)
    assert run.recovery_count == 1

    restricted = Port(restricted=True)
    blocked_engine, blocked_scope, blocked_item, blocked_plan = ready_engine(restricted)
    blocked = execution(blocked_item, blocked_plan)
    blocked_engine.enqueue(blocked, blocked_scope)
    assert blocked_engine.execute_next(blocked_scope).status is ExecutionStatus.BLOCKED
    with pytest.raises(PermissionError, match="restriction"):
        blocked_engine.recover(blocked.id, blocked_scope)


def test_graceful_stop_queues_dashboard_api_metrics_and_module_boundary() -> None:
    engine, request_scope, item, plan = ready_engine()
    run = execution(item, plan)
    engine.enqueue(run, request_scope)
    engine.graceful_stop(run.id, request_scope)
    assert run.status is ExecutionStatus.STOPPED
    assert set(engine.dashboard(request_scope)["sections"]) == {
        "Automations",
        "Plans",
        "Executions",
        "Triggers",
        "Conditions",
        "Queues",
        "Monitoring",
        "Recovery",
        "Analytics",
    }

    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    register_automation_routes(app, engine)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/automation/dashboard" in app.routes
    rendered = engine.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
    assert APPROVED_MODULES == {
        "runtime_manager",
        "resource_center",
        "task_scheduler",
        "browser_cluster",
        "device_center",
        "account_center",
        "browser_runtime",
        "proxy_center",
        "workflow_center",
        "operations_center",
        "risk_control",
        "publishing_center",
        "data_collection",
        "interaction_center",
        "analytics_center",
        "local_runtime",
    }
    with pytest.raises(ValueError):
        ExecutionStep("bad", "instagram", "mass-action").validate()
