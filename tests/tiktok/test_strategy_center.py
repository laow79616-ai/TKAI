from datetime import timedelta

import pytest

from tiktok.strategy_center.adapters import INPUT_MODULES
from tiktok.strategy_center.api import ROUTES, register_strategy_center_routes
from tiktok.strategy_center.metrics import METRIC_NAMES
from tiktok.strategy_center.models import (
    ApprovalDecision,
    ApprovalType,
    HandoffType,
    ObjectiveType,
    PlanningHorizon,
    ReviewType,
    ScenarioType,
    Strategy,
    StrategyApproval,
    StrategyConstraint,
    StrategyHandoff,
    StrategyObjective,
    StrategyReview,
    StrategyScenario,
    StrategyScope,
    StrategyStatus,
    StrategyType,
    utcnow,
)
from tiktok.strategy_center.service import TikTokAutonomousStrategyCenter


class Input:
    read_only = True

    def __init__(self, **values: object) -> None:
        self.values = {
            "status": "healthy",
            "health": 0.8,
            "capacity": 0.7,
            "risk": 0.2,
            "historical_score": 0.75,
            "source": "bounded-test-double",
            **values,
        }

    def snapshot(self, scope: StrategyScope) -> dict[str, object]:
        return dict(self.values)


def scope(workspace: str = "workspace") -> StrategyScope:
    return StrategyScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:strategy-center:admin"}),
    )


def strategy(reference: str = "strategy-1", workspace: str = "workspace") -> Strategy:
    return Strategy(
        reference,
        "Reliability strategy",
        "Improve bounded publishing reliability",
        "tenant",
        workspace,
        "operator",
        StrategyType.PUBLISHING,
        PlanningHorizon.WEEKLY,
        2,
        [StrategyObjective(ObjectiveType.PUBLISHING_RELIABILITY, 0.9, "ratio")],
        [StrategyConstraint("publishing_limit", 1, 10, 3, "jobs")],
    )


def service(**input_values: object) -> TikTokAutonomousStrategyCenter:
    return TikTokAutonomousStrategyCenter(
        {name: Input(**input_values) for name in INPUT_MODULES}
    )


def approve(
    center: TikTokAutonomousStrategyCenter,
    approval_id: str = "approval-1",
) -> StrategyApproval:
    approval = StrategyApproval(
        approval_id,
        "strategy-1",
        "tenant",
        "workspace",
        ApprovalType.STRATEGY,
        ApprovalDecision.APPROVED,
        "reviewer",
        "Bounded proposal approved",
        utcnow() + timedelta(hours=1),
    )
    return center.decide(approval, scope())


def test_crud_lifecycle_analysis_options_evaluation_and_recommendation() -> None:
    center = service()
    created = center.create_strategy(strategy(), scope())
    center.update_strategy(created.id, {"priority": 1}, scope())
    recommendation = center.analyze(created.id, scope())
    assert created.status is StrategyStatus.PROPOSED
    assert recommendation.advisory is True
    assert 0 <= recommendation.confidence <= 1
    assert recommendation.evidence_references
    assert len(center.contexts) == 1
    assert len(center.options) >= 5
    assert len(center.evaluations) == len(center.options)
    assert all(item.bounded for item in center.options.values())


def test_bounds_metadata_custom_horizon_and_unsafe_strategy_validation() -> None:
    item = strategy()
    item.constraints[0].requested = 100
    with pytest.raises(ValueError, match="bounds"):
        item.validate()
    item = strategy()
    item.metadata = {"token": "secret"}
    with pytest.raises(ValueError, match="Secrets"):
        item.validate()
    item = strategy()
    item.planning_horizon = PlanningHorizon.CUSTOM_BOUNDED
    with pytest.raises(ValueError, match="bounded window"):
        item.validate()
    item = strategy()
    item.description = "CAPTCHA bypass strategy"
    with pytest.raises(ValueError, match="Unsafe"):
        service().create_strategy(item, scope())


def test_read_only_inputs_and_safety_states_stop_analysis() -> None:
    class MutableInput(Input):
        read_only = False

    with pytest.raises(ValueError, match="read-only"):
        TikTokAutonomousStrategyCenter({"risk_control": MutableInput()})
    for state in (
        "restriction_active",
        "challenge_unresolved",
        "kill_switch_active",
        "workspace_paused",
        "account_paused",
    ):
        center = service(**{state: True})
        center.create_strategy(strategy(), scope())
        with pytest.raises(PermissionError, match="safety state"):
            center.analyze("strategy-1", scope())


def test_scenarios_are_bounded_offline_and_secret_safe() -> None:
    center = service()
    center.create_strategy(strategy(), scope())
    scenario = StrategyScenario(
        "scenario-1",
        "strategy-1",
        "tenant",
        "workspace",
        ScenarioType.WHAT_IF,
        {"capacity": 4},
    )
    assert center.simulate(scenario, scope()).result == {
        "dry_run": True,
        "bounded": True,
        "advisory": True,
        "strategy_type": "publishing_strategy",
    }
    live = StrategyScenario(
        "scenario-2",
        "strategy-1",
        "tenant",
        "workspace",
        ScenarioType.DRY_RUN,
        {},
        live_tiktok_access=True,
    )
    with pytest.raises(ValueError, match="live TikTok"):
        center.simulate(live, scope())


def test_approval_and_reference_only_handoff_enforcement() -> None:
    center = service()
    center.create_strategy(strategy(), scope())
    recommendation = center.analyze("strategy-1", scope())
    with pytest.raises(PermissionError, match="Approved"):
        center.handoff(
            StrategyHandoff(
                "handoff-1",
                "strategy-1",
                "tenant",
                "workspace",
                HandoffType.MISSION_ENGINE,
                recommendation.id,
                "approval-1",
            ),
            scope(),
        )
    approval = approve(center)
    handoff = StrategyHandoff(
        "handoff-1",
        "strategy-1",
        "tenant",
        "workspace",
        HandoffType.MISSION_ENGINE,
        recommendation.id,
        approval.id,
    )
    accepted = center.handoff(handoff, scope())
    assert accepted.reference_only is True
    assert accepted.accepted_reference.startswith("reference-only://")
    assert center.strategies["strategy-1"].status is StrategyStatus.ACTIVE_REFERENCE


def test_kill_switch_workspace_pause_scope_and_rbac() -> None:
    center = service()
    center.create_strategy(strategy(), scope())
    recommendation = center.analyze("strategy-1", scope())
    approval = approve(center)
    center.kill_switches.add(("tenant", "workspace"))
    handoff = StrategyHandoff(
        "handoff-1",
        "strategy-1",
        "tenant",
        "workspace",
        HandoffType.OPERATIONS_PLANNER,
        recommendation.id,
        approval.id,
    )
    with pytest.raises(PermissionError, match="Kill switch"):
        center.handoff(handoff, scope())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.get_strategy("strategy-1", scope("other"))
    viewer = StrategyScope("tenant", "workspace", "viewer")
    with pytest.raises(PermissionError, match="RBAC"):
        center.update_strategy("strategy-1", {"priority": 2}, viewer)


def test_reviews_history_analytics_dashboard_api_metrics_and_openapi() -> None:
    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.paths.append(path)

    center = service()
    center.create_strategy(strategy(), scope())
    center.analyze("strategy-1", scope())
    review = StrategyReview(
        "review-1",
        "strategy-1",
        "tenant",
        "workspace",
        "reviewer",
        ReviewType.STRATEGY,
        "Explainable proposal review",
        ["Keep limits"],
        ["Compare observed outcomes"],
    )
    center.add_review(review, scope())
    dashboard = center.dashboard(scope())
    assert dashboard["advisory_only"] is True
    assert dashboard["title"] == "TikTok Autonomous Strategy Center"
    assert len(dashboard["sections"]) == 14
    assert center.analytics(scope())["strategies_total"] == 1
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
    app = App()
    register_strategy_center_routes(app, center)
    assert set(ROUTES).issubset(app.paths)
    assert "/tiktok/strategy-center/dashboard" in app.paths
    assert "/tiktok/strategy-center/metrics" in app.paths
