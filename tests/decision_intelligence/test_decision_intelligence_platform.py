import pytest

from decision_intelligence import (
    Alternative,
    ApprovalStatus,
    Decision,
    DecisionContext,
    DecisionIntelligencePlatform,
    DecisionScope,
    DecisionStatus,
    Objective,
    Priority,
)
from decision_intelligence.dashboard import SECTIONS


@pytest.fixture
def system() -> tuple[DecisionIntelligencePlatform, DecisionScope]:
    platform = DecisionIntelligencePlatform()
    scope = DecisionScope(
        "tenant-a",
        "workspace-a",
        "owner",
        frozenset({"decision_intelligence:admin"}),
    )
    platform.create_decision(
        Decision(
            "decision-1",
            "Select operating model",
            "Choose the strongest enterprise operating model.",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "strategy",
            Priority.HIGH,
            context=DecisionContext(
                business_context={"growth": "international"},
                assumptions=("Demand remains stable.",),
            ),
            objectives=[
                Objective(
                    "objective-1",
                    "Maximize value",
                    True,
                    1,
                    {"roi": 20},
                    ("ROI exceeds 20%.",),
                    "P1Y",
                    1_000_000,
                )
            ],
            alternatives=[
                Alternative(
                    "build",
                    "Build",
                    estimated_cost=300,
                    estimated_benefit=800,
                    risk=0.3,
                    confidence=0.9,
                    trade_offs=("Longer delivery",),
                ),
                Alternative(
                    "buy",
                    "Buy",
                    estimated_cost=450,
                    estimated_benefit=850,
                    risk=0.2,
                    confidence=0.8,
                    trade_offs=("Vendor dependency",),
                ),
            ],
        ),
        scope,
    )
    return platform, scope


def test_decision_lifecycle_approval_and_metrics(
    system: tuple[DecisionIntelligencePlatform, DecisionScope],
) -> None:
    platform, scope = system
    platform.set_status("decision-1", DecisionStatus.PROPOSED, scope)
    platform.set_status("decision-1", DecisionStatus.UNDER_REVIEW, scope)
    approval = platform.request_approval("decision-1", ("owner",), scope)
    platform.review_approval(
        approval.id, ApprovalStatus.APPROVED, "Evidence accepted.", scope
    )
    platform.set_status("decision-1", DecisionStatus.APPROVED, scope)
    platform.set_status("decision-1", DecisionStatus.EXECUTED, scope)
    platform.set_status("decision-1", DecisionStatus.ARCHIVED, scope)
    platform.set_status("decision-1", DecisionStatus.DELETED, scope)
    assert platform.metrics.snapshot()["decision_execution_success_total"] == 1
    assert platform.audit


def test_evaluation_recommendation_explanation_and_insight(
    system: tuple[DecisionIntelligencePlatform, DecisionScope],
) -> None:
    platform, scope = system
    evaluation = platform.evaluate(
        "decision-1",
        {"value": 0.6, "delivery": 0.4},
        {
            "build": {"value": 90, "delivery": 70},
            "buy": {"value": 80, "delivery": 95},
        },
        scope,
        scenario_comparison={"base": "build", "accelerated": "buy"},
    )
    recommendation = platform.recommend(
        "decision-1",
        evaluation.id,
        scope,
        evidence_references=("evidence://analysis/42",),
    )
    assert recommendation.ranked_options == ("build", "buy")
    explanation = platform.explain(
        recommendation.id, "reasoning://trace/42", scope
    )
    assert explanation.evidence_references == ("evidence://analysis/42",)
    insight = platform.generate_insight("decision-1", scope)
    assert insight.decision_quality == 1
    assert set(SECTIONS) <= platform.dashboard(scope).keys()


def test_simulation_forecast_and_metrics(
    system: tuple[DecisionIntelligencePlatform, DecisionScope],
) -> None:
    platform, scope = system
    simulation = platform.simulate(
        "decision-1", {"revenue": 25, "cost": -5}, scope,
        baseline={"revenue": 100, "cost": 50},
    )
    assert simulation.forecast == {"revenue": 125, "cost": 45}
    assert simulation.rollback_impact == {
        "restore": {"revenue": 100, "cost": 50}
    }
    assert platform.metrics.snapshot()["decision_simulations_total"] == 1


def test_validation_isolation_rbac_and_sensitive_data() -> None:
    platform = DecisionIntelligencePlatform()
    admin = DecisionScope(
        "tenant-a",
        "workspace-a",
        "owner",
        frozenset({"decision_intelligence:admin"}),
    )
    with pytest.raises(ValueError, match="Sensitive"):
        platform.create_decision(
            Decision(
                "unsafe",
                "Unsafe",
                "Contains secret",
                admin.tenant,
                admin.workspace,
                admin.actor,
                "security",
                metadata={"api_token": "never"},
            ),
            admin,
        )
    platform.create_decision(
        Decision(
            "safe",
            "Safe",
            "Scoped",
            admin.tenant,
            admin.workspace,
            admin.actor,
            "security",
        ),
        admin,
    )
    attacker = DecisionScope(
        "tenant-b",
        "workspace-a",
        "attacker",
        frozenset({"decision_intelligence:admin"}),
    )
    with pytest.raises(PermissionError):
        platform.set_status("safe", DecisionStatus.PROPOSED, attacker)
    with pytest.raises(PermissionError, match="RBAC"):
        platform.set_status(
            "safe",
            DecisionStatus.PROPOSED,
            DecisionScope("tenant-a", "workspace-a", "reader"),
        )


def test_evaluation_validation(
    system: tuple[DecisionIntelligencePlatform, DecisionScope],
) -> None:
    platform, scope = system
    with pytest.raises(ValueError, match="sum to one"):
        platform.evaluate(
            "decision-1",
            {"value": 0.9},
            {"build": {"value": 80}, "buy": {"value": 70}},
            scope,
        )
    with pytest.raises(ValueError, match="every candidate"):
        platform.evaluate(
            "decision-1",
            {"value": 1},
            {"build": {"value": 80}},
            scope,
        )
