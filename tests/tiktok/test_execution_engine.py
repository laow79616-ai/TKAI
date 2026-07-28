"""Mocks-only coverage for the Enterprise TikTok AI Execution Engine."""

from __future__ import annotations

from typing import Any

import pytest

from tiktok.execution_engine.adapters import LocalMockInfrastructure
from tiktok.execution_engine.api import ROUTES
from tiktok.execution_engine.metrics import METRIC_NAMES
from tiktok.execution_engine.models import (
    INTEGRATION_MODULES,
    ExecutionPipeline,
    ExecutionPlan,
    ExecutionScope,
    ExecutionStatus,
    ExecutionStep,
    PipelineKind,
    StageKind,
    VerificationKind,
)
from tiktok.execution_engine.service import TikTokAIExecutionEngine


def scope(workspace: str = "workspace") -> ExecutionScope:
    return ExecutionScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:execution:admin"}),
    )


def plan(reference: str = "execution-1") -> ExecutionPlan:
    return ExecutionPlan(
        reference,
        "Approved local operation",
        "tenant",
        "workspace",
        "operator",
        "planner://approved/1",
        "workflow://1",
        "automation://1",
        "runtime://1",
        metadata={"purpose": "bounded test"},
    )


def pipeline(
    execution_id: str = "execution-1",
    kind: PipelineKind = PipelineKind.CHECKPOINTED,
) -> ExecutionPipeline:
    return ExecutionPipeline(
        f"pipeline-{execution_id}",
        execution_id,
        "tenant",
        "workspace",
        kind,
        [
            ExecutionStep(
                "prepare",
                "Prepare workflow",
                "workflow_center",
                "prepare",
                checkpoint_after=True,
                rollback_action="release",
            ),
            ExecutionStep(
                "run",
                "Run approved automation",
                "automation_engine",
                "execute_approved",
                depends_on=["prepare"],
                maximum_attempts=2,
                rollback_action="rollback",
            ),
        ],
    )


class MockInfrastructure(LocalMockInfrastructure):
    def __init__(self) -> None:
        self.validations: list[VerificationKind] = []
        self.dispatched: list[str] = []
        self.rolled_back: list[str] = []
        self.cleaned: list[str] = []

    def validate(
        self,
        kind: VerificationKind,
        execution: ExecutionPlan,
        request_scope: ExecutionScope,
    ) -> tuple[bool, str]:
        self.validations.append(kind)
        return True, "approved"

    def dispatch(
        self, step: ExecutionStep, request_scope: ExecutionScope
    ) -> dict[str, Any]:
        self.dispatched.append(step.id)
        return {"accepted": True, "reference": f"result://{step.id}"}

    def rollback(
        self,
        step: ExecutionStep,
        result_reference: str,
        request_scope: ExecutionScope,
    ) -> None:
        self.rolled_back.append(step.id)

    def cleanup(self, execution_id: str, request_scope: ExecutionScope) -> None:
        self.cleaned.append(execution_id)


class RejectingInfrastructure(MockInfrastructure):
    def validate(
        self,
        kind: VerificationKind,
        execution: ExecutionPlan,
        request_scope: ExecutionScope,
    ) -> tuple[bool, str]:
        return kind is not VerificationKind.APPROVAL, "approval missing"


class FailingInfrastructure(MockInfrastructure):
    def dispatch(
        self, step: ExecutionStep, request_scope: ExecutionScope
    ) -> dict[str, Any]:
        if step.id == "run":
            raise RuntimeError("bounded mock failure")
        return super().dispatch(step, request_scope)


def create(
    infrastructure: LocalMockInfrastructure | None = None,
) -> TikTokAIExecutionEngine:
    service = TikTokAIExecutionEngine(infrastructure)
    service.create_plan(plan(), pipeline(), scope())
    return service


def test_lifecycle_validation_dispatch_execution_checkpoints_and_results() -> None:
    adapter = MockInfrastructure()
    service = create(adapter)
    assert service.plans["execution-1"].approved_plan_reference.startswith(
        "sealed-ref://"
    )
    service.validate("execution-1", scope())
    assert len(adapter.validations) == len(VerificationKind)
    service.enqueue("execution-1", scope())
    completed = service.dispatch("execution-1", scope())
    assert completed.status is ExecutionStatus.COMPLETED
    assert adapter.dispatched == ["prepare", "run"]
    assert service.checkpoints
    assert len(service.results) == 2
    assert all(
        service.stages[f"execution-1:{kind.value}"].progress == 100
        for kind in StageKind
    )


def test_approval_validation_failure_stops_queue_and_dispatch() -> None:
    service = create(RejectingInfrastructure())
    with pytest.raises(PermissionError, match="approval_validation"):
        service.validate("execution-1", scope())
    assert service.plans["execution-1"].status is ExecutionStatus.FAILED
    assert not service.queue


def test_failure_rollback_cleanup_monitoring_and_analytics() -> None:
    adapter = FailingInfrastructure()
    service = create(adapter)
    service.validate("execution-1", scope())
    service.enqueue("execution-1", scope())
    assert service.dispatch("execution-1", scope()).status is ExecutionStatus.FAILED
    assert service.monitoring(scope())["failure_detection"] == 1
    assert service.analytics(scope())["execution_failure"] == 1
    rolled_back = service.rollback("execution-1", scope())
    assert rolled_back.status is ExecutionStatus.ROLLED_BACK
    assert adapter.rolled_back == ["prepare"]
    assert adapter.cleaned
    assert service.metrics.values["tiktok_execution_rollbacks"] == 1


def test_recovery_requires_checkpoint_and_requeues() -> None:
    service = create()
    service.validate("execution-1", scope())
    service.enqueue("execution-1", scope())
    service.dispatch("execution-1", scope())
    service.plans["execution-1"].status = ExecutionStatus.FAILED
    recovered = service.recover("execution-1", scope())
    assert recovered.status is ExecutionStatus.QUEUED
    assert recovered.id in service.queue
    assert service.metrics.values["tiktok_execution_recoveries"] == 1


def test_security_isolation_rbac_bounds_and_forbidden_actions() -> None:
    service = TikTokAIExecutionEngine()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.create_plan(plan(), pipeline(), scope("other"))
    unsafe = pipeline()
    unsafe.steps[0].action = "captcha_bypass"
    with pytest.raises(ValueError, match="forbidden"):
        service.create_plan(plan(), unsafe, scope())
    secret = plan()
    secret.metadata = {"token": "no"}
    with pytest.raises(ValueError, match="Secrets"):
        service.create_plan(secret, pipeline(), scope())
    no_write = ExecutionScope("tenant", "workspace", "reader")
    with pytest.raises(PermissionError, match="write"):
        service.create_plan(plan(), pipeline(), no_write)


@pytest.mark.parametrize("kind", list(PipelineKind))
def test_all_pipeline_contracts_are_bounded(kind: PipelineKind) -> None:
    candidate = pipeline(kind=kind)
    candidate.maximum_concurrency = 2 if kind is PipelineKind.PARALLEL else 1
    candidate.validate()
    assert len(candidate.steps) <= 100
    assert candidate.maximum_concurrency <= 10


def test_integration_dashboard_api_and_metrics_contracts() -> None:
    service = create()
    dashboard = service.dashboard(scope())
    assert len(INTEGRATION_MODULES) == 11
    assert len(ROUTES) == 7
    assert dashboard["sections"] == [
        "Execution Overview",
        "Pipelines",
        "Stages",
        "Workers",
        "Checkpoints",
        "Rollback",
        "Results",
        "Monitoring",
        "Analytics",
    ]
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
