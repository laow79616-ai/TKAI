from datetime import timedelta

import pytest

from tiktok.operations_planner.adapters import INPUT_MODULES
from tiktok.operations_planner.metrics import METRIC_NAMES
from tiktok.operations_planner.models import (
    Approval,
    ApprovalDecision,
    ApprovalKind,
    Bound,
    ExecutionHandoff,
    Objective,
    ObjectiveKind,
    OperationsPlan,
    PlannerScope,
    PlanningHorizon,
    PlanStatus,
    Simulation,
    SimulationKind,
    StrategyKind,
    utcnow,
)
from tiktok.operations_planner.service import TikTokAIOperationsPlanner


class Input:
    def __init__(self, **value: object) -> None:
        self.value = {"status": "healthy", "capacity": 4, **value}

    def snapshot(self, scope: PlannerScope) -> dict[str, object]:
        return dict(self.value)


class Handoff:
    def accept(self, handoff: ExecutionHandoff, scope: PlannerScope) -> str:
        return f"accepted://{handoff.id}"


def scope(workspace: str = "w") -> PlannerScope:
    return PlannerScope(
        "tenant", workspace, "operator", frozenset({"tiktok:planner:admin"})
    )


def plan(reference: str = "p", workspace: str = "w") -> OperationsPlan:
    return OperationsPlan(
        reference,
        "Daily reliability",
        "bounded",
        "tenant",
        workspace,
        "owner",
        PlanningHorizon.DAILY,
        2,
        [Objective(ObjectiveKind.PUBLISHING_RELIABILITY, 95, "percent")],
        StrategyKind.CONSERVATIVE,
        [Bound("worker_capacity", 1, 10, 4)],
    )


def approval(reference: str = "approval", plan_id: str = "p") -> Approval:
    return Approval(
        reference,
        plan_id,
        "tenant",
        "w",
        ApprovalKind.PLAN,
        ApprovalDecision.APPROVED,
        "reviewer",
        "bounded and safe",
        utcnow() + timedelta(hours=1),
    )


def test_lifecycle_planning_approval_and_reference_handoff() -> None:
    service = TikTokAIOperationsPlanner(
        {name: Input() for name in INPUT_MODULES},
        {
            name: Handoff()
            for name in ("automation", "workflow", "scheduler", "resources", "runtime")
        },
    )
    service.create_plan(plan(), scope())
    recommendation = service.analyze("p", scope())
    assert recommendation.advisory is True
    assert recommendation.concurrency == 3
    assert service.plans["p"].status is PlanStatus.PROPOSED
    service.transition("p", PlanStatus.PENDING_REVIEW, scope())
    service.decide(approval(), scope())
    service.transition("p", PlanStatus.APPROVED, scope())
    service.transition("p", PlanStatus.SCHEDULED, scope())
    result = service.handoff(
        ExecutionHandoff(
            "e",
            "p",
            "tenant",
            "w",
            "auto://p",
            "workflow://p",
            ["task://1"],
            ["resource://1"],
            "daily",
            ["checkpoint"],
            "pause and restore checkpoint",
        ),
        scope(),
    )
    assert set(result.accepted_references) == {
        "automation",
        "workflow",
        "scheduler",
        "resources",
        "runtime",
    }
    assert service.plans["p"].status is PlanStatus.EXECUTING


def test_bounds_secrets_isolation_and_approval_are_enforced() -> None:
    service = TikTokAIOperationsPlanner()
    invalid = plan()
    invalid.constraints[0].requested = 100
    with pytest.raises(ValueError, match="bounds"):
        service.create_plan(invalid, scope())
    secret = plan("secret")
    secret.metadata = {"cookie": "not-allowed"}
    with pytest.raises(ValueError, match="Secrets"):
        service.create_plan(secret, scope())
    service.create_plan(plan(), scope())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.update_plan("p", {"name": "x"}, scope("other"))
    service.transition("p", PlanStatus.ANALYZING, scope())
    service.transition("p", PlanStatus.PROPOSED, scope())
    service.transition("p", PlanStatus.PENDING_REVIEW, scope())
    with pytest.raises(PermissionError, match="approval"):
        service.transition("p", PlanStatus.APPROVED, scope())


def test_restrictions_challenges_simulation_and_kill_switch() -> None:
    inputs = {name: Input() for name in INPUT_MODULES}
    inputs["risk"] = Input(restriction_active=True)
    service = TikTokAIOperationsPlanner(inputs)
    service.create_plan(plan(), scope())
    with pytest.raises(PermissionError, match="restriction"):
        service.analyze("p", scope())
    simulation = Simulation(
        "s", "p", "tenant", "w", SimulationKind.DRY_RUN, {}, {}, live_access=True
    )
    with pytest.raises(ValueError, match="live TikTok"):
        service.simulate(simulation, scope())


def test_metrics_dashboard_and_api_contracts() -> None:
    from tiktok.operations_planner.api import ROUTES

    service = TikTokAIOperationsPlanner()
    service.create_plan(plan(), scope())
    dashboard = service.dashboard(scope())
    assert len(ROUTES) == 13
    assert "Approvals" in dashboard["sections"]
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
