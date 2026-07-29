from __future__ import annotations

import pytest

from reasoning_engine import (
    EnterpriseAIReasoningEngine,
    ExecutionLimits,
    LifecycleState,
    ReasoningMode,
    ReasoningScope,
)
from reasoning_engine.api import register_reasoning_routes
from reasoning_engine.dashboard import SECTIONS

PERMISSIONS = {
    "reasoning:read",
    "reasoning:write",
    "reasoning:execute",
    "reasoning:plan",
    "reasoning:decide",
    "reasoning:validate",
    "reasoning:simulate",
    "reasoning:optimize",
}


def configured(
    limits: ExecutionLimits | None = None,
) -> tuple[EnterpriseAIReasoningEngine, ReasoningScope]:
    engine = EnterpriseAIReasoningEngine(limits=limits)
    scope = ReasoningScope("tenant-a", "workspace-a", "alice")
    engine.security.grant(scope, PERMISSIONS)
    return engine, scope


def session(engine: EnterpriseAIReasoningEngine, scope: ReasoningScope) -> str:
    return engine.create_session(
        {
            "id": "reasoning-1",
            "agent": "support-agent",
            "goal": "Resolve the customer issue",
            "strategy": "risk-aware",
            "mode": "planning",
            "priority": 80,
            "metadata": {"request": "case-1"},
        },
        scope,
    ).id


def plan(engine: EnterpriseAIReasoningEngine, scope: ReasoningScope) -> str:
    identifier = session(engine, scope)
    engine.create_plan(
        identifier,
        [
            {"id": "research", "goal": "Research", "priority": 80},
            {
                "id": "resolve",
                "goal": "Resolve",
                "dependencies": ["research"],
                "priority": 90,
            },
        ],
        scope,
    )
    return identifier


def test_session_modes_lifecycle_dashboard_audit_and_metrics() -> None:
    engine, scope = configured()
    identifier = session(engine, scope)
    created = engine.get(identifier, scope)
    assert created.mode is ReasoningMode.PLANNING
    for state in (
        LifecycleState.PREPARED,
        LifecycleState.RUNNING,
        LifecycleState.VALIDATED,
        LifecycleState.COMPLETED,
        LifecycleState.ARCHIVED,
    ):
        engine.transition(identifier, state, scope)
    assert set(SECTIONS) <= set(engine.dashboard(scope)["sections"])
    assert engine.metrics.snapshot()["reasoning_sessions_total"] == 1
    assert any(
        event["action"] == "reasoning:created" for event in engine.security.audit
    )


@pytest.mark.parametrize("mode", [item.value for item in ReasoningMode])
def test_all_reasoning_modes(mode: str) -> None:
    engine, scope = configured()
    created = engine.create_session(
        {"agent": "agent", "goal": "goal", "mode": mode}, scope
    )
    assert created.mode.value == mode


def test_planning_dependencies_priority_and_loop_detection() -> None:
    engine, scope = configured()
    identifier = plan(engine, scope)
    created = engine.explain(identifier, scope)["plan"]
    assert created is not None
    assert created["execution_plan"] == ["research", "resolve"]
    with pytest.raises(ValueError, match="loop"):
        engine.planner.create(
            "cyclic",
            [
                {"id": "a", "dependencies": ["b"]},
                {"id": "b", "dependencies": ["a"]},
            ],
        )


def test_decision_ranking_threshold_confidence_and_fallback() -> None:
    engine, scope = configured()
    identifier = session(engine, scope)
    decision = engine.decide(
        identifier,
        [
            {"option": "safe", "scores": {"risk": 0.9, "value": 0.7}},
            {"option": "fast", "score": 0.6},
        ],
        scope,
        threshold=0.7,
        fallback="manual",
        rules=["prefer-safe"],
    )
    assert decision.option == "safe"
    assert decision.ranking[0][0] == "safe"
    fallback = engine.decision_engine.decide(
        [{"option": "unsafe", "score": 0.2}], threshold=0.8, fallback="manual"
    )
    assert fallback.option == "manual"


def test_validation_simulation_optimization_and_explanation() -> None:
    engine, scope = configured()
    identifier = plan(engine, scope)
    invalid = engine.validate(identifier, {"safe": False}, scope)
    assert not invalid.valid
    assert engine.metrics.snapshot()["reasoning_validation_failures_total"] == 1
    simulations = engine.simulate(
        identifier,
        [
            {
                "scenario": "regional failover",
                "variables": {"availability": 0.99, "cost": 0.5},
                "baselines": {"availability": 0.95, "cost": 0.4},
                "rollback_plan": ["restore primary"],
            }
        ],
        scope,
    )
    assert simulations[0].comparison["availability"] == pytest.approx(0.04)
    optimized = engine.optimize(
        identifier,
        {"cpu": 2, "memory": 6},
        scope,
        cost_per_unit=2,
        latency_per_task=0.5,
    )
    assert optimized.resource["memory"] == 0.75
    assert optimized.estimated_cost == 16
    assert engine.explain(identifier, scope)["optimization"] is not None


def test_tenant_workspace_rbac_and_execution_limits() -> None:
    engine, scope = configured(ExecutionLimits(max_subtasks=1, max_simulations=1))
    identifier = session(engine, scope)
    other_tenant = ReasoningScope("tenant-b", "workspace-a", "alice")
    other_workspace = ReasoningScope("tenant-a", "workspace-b", "alice")
    engine.security.grant(other_tenant, {"reasoning:read"})
    engine.security.grant(other_workspace, {"reasoning:read"})
    with pytest.raises(PermissionError, match="Cross-tenant"):
        engine.get(identifier, other_tenant)
    with pytest.raises(PermissionError, match="Cross-workspace"):
        engine.get(identifier, other_workspace)
    with pytest.raises(ValueError, match="subtask"):
        engine.create_plan(identifier, [{"id": "a"}, {"id": "b"}], scope)
    unprivileged = ReasoningScope("tenant-a", "workspace-a", "bob")
    with pytest.raises(PermissionError, match="reasoning:write"):
        engine.create_session({"agent": "agent", "goal": "goal"}, unprivileged)


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_and_metrics_contract() -> None:
    app = App()
    engine, _ = configured()
    register_reasoning_routes(app, engine)
    for path in (
        "/reasoning",
        "/reasoning/plans",
        "/reasoning/decisions",
        "/reasoning/validation",
        "/reasoning/simulation",
    ):
        assert any(route_path == path for _, route_path in app.routes)
    for metric in (
        "reasoning_sessions_total",
        "reasoning_plans_total",
        "reasoning_decisions_total",
        "reasoning_validation_failures_total",
        "reasoning_duration_seconds",
        "reasoning_simulations_total",
    ):
        assert metric in engine.metrics.render_prometheus()
