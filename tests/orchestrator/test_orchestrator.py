from __future__ import annotations

import pytest

from orchestrator import EnterpriseAIOrchestrator, ExecutionState, RouteType, Scope
from orchestrator.api import register_orchestrator_routes
from orchestrator.dashboard import SECTIONS
from orchestrator.models import PlanStep
from orchestrator.policies import PolicySet, RetryPolicy
from orchestrator.queue import ExecutionQueue


def configured(*, attempts: int = 2) -> tuple[EnterpriseAIOrchestrator, Scope]:
    service = EnterpriseAIOrchestrator(
        policies=PolicySet(retry=RetryPolicy(attempts=attempts))
    )
    scope = Scope("tenant-a", "alice")
    service.security.grant(scope, {"plan:create", "execution:run"})
    return service, scope


def payload() -> dict[str, object]:
    return {
        "id": "plan-1",
        "name": "Enterprise plan",
        "description": "Route enterprise work",
        "priority": 80,
        "dependencies": [],
        "metadata": {"department": "engineering"},
        "steps": [
            {
                "id": "knowledge",
                "name": "Retrieve",
                "route": "knowledge",
                "target": "kb",
            },
            {
                "id": "agent",
                "name": "Reason",
                "route": "single_agent",
                "target": "agent-1",
                "dependencies": ["knowledge"],
            },
        ],
    }


def test_planner_router_coordinator_execution_checkpoint_and_dashboard() -> None:
    service, scope = configured()
    service.register(RouteType.KNOWLEDGE, lambda step, context: ["document"])
    service.register(
        RouteType.SINGLE_AGENT,
        lambda step, context: {"answer": step.target},
    )
    plan = service.create_plan(payload(), scope)
    execution = service.submit(plan.id, scope)
    completed = service.execute(execution.id, scope)

    assert completed.state is ExecutionState.COMPLETED
    assert completed.results["knowledge"] == ["document"]
    assert completed.checkpoint_id
    assert set(SECTIONS) <= set(service.dashboard(scope)["sections"])
    assert service.metrics.snapshot()["checkpoint_total"] == 2
    assert service.coordinator.snapshot()["active"] == 0


def test_retry_failure_dead_letter_recovery_resume_rollback_and_cancel() -> None:
    service, scope = configured()
    calls = 0

    def handler(step: PlanStep, context: dict[str, object]) -> str:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise RuntimeError("transient")
        return step.id

    service.register(RouteType.KNOWLEDGE, handler)
    service.register(RouteType.SINGLE_AGENT, handler)
    plan = service.create_plan(payload(), scope)
    execution = service.submit(plan.id, scope)
    result = service.execute(execution.id, scope)
    assert result.state is ExecutionState.COMPLETED
    assert service.metrics.snapshot()["execution_retry_total"] == 1

    checkpoint_id = result.checkpoint_id
    assert checkpoint_id is not None
    resumed = service.resume(result.id, scope, checkpoint_id)
    assert resumed.state is ExecutionState.COMPLETED
    assert service.rollback(result.id, scope).state is ExecutionState.ROLLED_BACK

    cancelled = service.cancel(service.submit(plan.id, scope).id, scope)
    assert cancelled.state is ExecutionState.CANCELLED

    failing, failing_scope = configured(attempts=1)
    failing.register(
        RouteType.KNOWLEDGE,
        lambda step, context: (_ for _ in ()).throw(RuntimeError("failed")),
    )
    failed_plan = failing.create_plan(payload(), failing_scope)
    failed = failing.execute(
        failing.submit(failed_plan.id, failing_scope).id, failing_scope
    )
    assert failed.state is ExecutionState.FAILED
    assert failing.queue.dead_letters == (failed.id,)


def test_queue_priority_delay_and_security_isolation_and_secrets() -> None:
    queue = ExecutionQueue()
    queue.put("low", 10)
    queue.put("high", 100)
    queue.put("delayed", 100, available_at=10)
    assert queue.pop(0) == "high"
    assert queue.pop(0) == "low"
    assert queue.pop(0) is None
    assert queue.pop(10) == "delayed"

    service, scope = configured()
    with pytest.raises(ValueError):
        service.create_plan({**payload(), "metadata": {"secret": "raw"}}, scope)
    plan = service.create_plan(
        {**payload(), "metadata": {"secret": "secret://vault/key"}}, scope
    )
    with pytest.raises(PermissionError):
        service.submit(plan.id, Scope("tenant-b", "alice"))


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_and_metrics_contract() -> None:
    app = App()
    service, _ = configured()
    register_orchestrator_routes(app, service)
    for path in (
        "/orchestrator",
        "/plans",
        "/executions",
        "/queues",
        "/checkpoints",
        "/recovery",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    rendered = service.metrics.render_prometheus()
    for metric in (
        "execution_plans_total",
        "execution_total",
        "execution_failed_total",
        "execution_retry_total",
        "queue_depth",
        "checkpoint_total",
        "recovery_total",
    ):
        assert metric in rendered
