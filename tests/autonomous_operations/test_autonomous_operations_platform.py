import pytest

from autonomous_operations import (
    AutonomousOperation,
    AutonomousOperationsPlatform,
    ExecutionStatus,
    Feedback,
    Objective,
    ObjectiveType,
    OperationMode,
    OperationScope,
    OperationStatus,
    Policy,
    PolicyType,
    SafetyConfig,
    Strategy,
    StrategyType,
    Task,
)


@pytest.fixture
def platform_and_scopes():
    platform = AutonomousOperationsPlatform()
    permissions = frozenset(
        {
            "autonomous_operations:read",
            "autonomous_operations:write",
            "autonomous_operations:execute",
            "autonomous_operations:approve",
        }
    )
    scope = OperationScope("tenant-a", "workspace-a", "owner", permissions)
    admin = OperationScope(
        "tenant-a", "workspace-a", "admin", frozenset({"autonomous_operations:admin"})
    )
    operation = AutonomousOperation(
        "op-1",
        "Availability loop",
        "Self-healing",
        "tenant-a",
        "workspace-a",
        "owner",
        10,
        OperationMode.AUTONOMOUS,
    )
    platform.create_operation(operation, scope)
    return platform, scope, admin, operation


def test_lifecycle_objectives_policies_and_strategies(platform_and_scopes):
    platform, scope, _, operation = platform_and_scopes
    platform.add_objective(
        Objective(
            "obj",
            operation.id,
            "tenant-a",
            "workspace-a",
            ObjectiveType.AVAILABILITY,
            99.9,
        ),
        scope,
    )
    platform.add_policy(
        Policy(
            "retry",
            operation.id,
            "tenant-a",
            "workspace-a",
            PolicyType.RETRY,
            {"limit": 1},
        ),
        scope,
    )
    platform.add_strategy(
        Strategy(
            "adaptive", operation.id, "tenant-a", "workspace-a", StrategyType.ADAPTIVE
        ),
        scope,
    )
    platform.set_status(operation.id, OperationStatus.LEARNING, scope)
    platform.set_status(operation.id, OperationStatus.READY, scope)
    assert operation.objective_ids == ("obj",)
    assert operation.policy_ids == ("retry",)
    assert operation.strategy_ids == ("adaptive",)
    with pytest.raises(ValueError):
        platform.set_status(operation.id, OperationStatus.DELETED, scope)


def test_execution_dependencies_retry_checkpoint_and_metrics(platform_and_scopes):
    platform, scope, _, operation = platform_and_scopes
    platform.set_status(operation.id, OperationStatus.READY, scope)
    platform.add_policy(
        Policy(
            "retry",
            operation.id,
            "tenant-a",
            "workspace-a",
            PolicyType.RETRY,
            {"limit": 1},
        ),
        scope,
    )
    platform.configure_tasks(
        operation.id,
        [Task("inspect", "inspect"), Task("repair", "repair", ("inspect",))],
        scope,
    )
    attempts = {"count": 0}

    def repair(task, context):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return {"repaired": True}

    platform.register_handler("repair", repair)
    execution = platform.execute(operation.id, {"risk": 0.1}, scope)
    assert execution.status is ExecutionStatus.SUCCEEDED
    assert execution.attempts == 3
    assert len(execution.checkpoints) == 2
    assert platform.metrics.snapshot()["autonomous_success_total"] == 1


def test_approval_rollback_and_safety(platform_and_scopes):
    platform, scope, admin, operation = platform_and_scopes
    operation.mode = OperationMode.SUPERVISED
    platform.set_status(operation.id, OperationStatus.READY, scope)
    platform.configure_safety(
        SafetyConfig(
            operation.id,
            "tenant-a",
            "workspace-a",
            approval_required=True,
            maximum_risk=0.4,
        ),
        scope,
    )
    platform.add_policy(
        Policy(
            "rollback", operation.id, "tenant-a", "workspace-a", PolicyType.ROLLBACK
        ),
        scope,
    )
    platform.configure_tasks(operation.id, [Task("task", "fail")], scope)
    waiting = platform.execute(operation.id, {"risk": 0.1}, scope)
    assert waiting.status is ExecutionStatus.WAITING_APPROVAL
    approval = platform.request_approval(operation.id, scope)
    platform.decide_approval(approval.id, True, scope)
    platform.register_handler(
        "fail", lambda task, context: (_ for _ in ()).throw(RuntimeError("failed"))
    )
    execution = platform.execute(operation.id, {"risk": 0.1}, scope, approval.id)
    assert execution.status is ExecutionStatus.ROLLED_BACK
    platform.set_kill_switch(operation.id, True, admin)
    with pytest.raises(PermissionError):
        platform.execute(operation.id, {"risk": 0.1}, scope, approval.id)


def test_feedback_optimization_adaptation_learning_dashboard(platform_and_scopes):
    platform, scope, _, operation = platform_and_scopes
    platform.record_feedback(
        Feedback(
            "fb",
            operation.id,
            "tenant-a",
            "workspace-a",
            {"latency": 1.2},
            confidence=0.6,
        ),
        scope,
    )
    optimized = platform.optimize(operation.id, scope)
    adapted = platform.adapt(
        operation.id, {"latency": 1.2, "load": 0.9, "confidence": 0.6}, scope
    )
    learned = platform.learn(operation.id, scope)
    dashboard = platform.dashboard(scope)
    assert optimized["energy_interface"] == "available"
    assert adapted["dynamic_routing"] and adapted["scaling"]
    assert learned["version"] == 1
    assert (
        set(
            (
                "operations",
                "objectives",
                "policies",
                "strategies",
                "executions",
                "feedback",
                "optimization",
                "learning",
                "safety",
            )
        )
        <= dashboard.keys()
    )


def test_security_isolation_policy_validation_and_no_secrets_in_audit(
    platform_and_scopes,
):
    platform, scope, _, operation = platform_and_scopes
    foreign = OperationScope(
        "tenant-b",
        "workspace-a",
        "intruder",
        frozenset({"autonomous_operations:read", "autonomous_operations:write"}),
    )
    assert platform.list_operations(foreign) == []
    with pytest.raises(PermissionError):
        platform.set_status(operation.id, OperationStatus.READY, foreign)
    with pytest.raises(ValueError):
        platform.add_policy(
            Policy(
                "unsafe",
                operation.id,
                "tenant-a",
                "workspace-a",
                PolicyType.EXECUTION,
                {"token": "raw"},
            ),
            scope,
        )
    assert "secret" not in str([item.to_dict() for item in platform.audit]).lower()
