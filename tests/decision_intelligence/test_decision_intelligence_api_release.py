from pathlib import Path

from decision_intelligence import (
    DecisionIntelligenceAPI,
    DecisionIntelligencePlatform,
    DecisionScope,
)


def test_api_contract() -> None:
    api = DecisionIntelligenceAPI(DecisionIntelligencePlatform())
    scope = DecisionScope("tenant", "workspace", "actor")
    assert set(api.ROUTES) == {
        "/decision-intelligence/decisions",
        "/decision-intelligence/evaluations",
        "/decision-intelligence/recommendations",
        "/decision-intelligence/approvals",
        "/decision-intelligence/simulations",
        "/decision-intelligence/insights",
    }
    assert api.get("/decision-intelligence/decisions", scope) == []


def test_release_structure_and_documentation() -> None:
    root = Path(__file__).parents[2]
    modules = (
        "decisions",
        "contexts",
        "objectives",
        "alternatives",
        "constraints",
        "evaluations",
        "scoring",
        "recommendations",
        "approvals",
        "policies",
        "explanations",
        "simulations",
        "insights",
        "dashboard",
        "api",
    )
    for module in modules:
        assert (
            root / "decision_intelligence" / module / "__init__.py"
        ).is_file()
    for document in (
        "Architecture",
        "DecisionLifecycle",
        "Evaluation",
        "Scoring",
        "Recommendations",
        "Approvals",
        "Simulations",
        "Insights",
        "Security",
        "Operations",
    ):
        assert (
            root / "docs" / "decision_intelligence" / f"{document}.md"
        ).is_file()
    assert "decision_intelligence*" in (
        root / "pyproject.toml"
    ).read_text("utf-8")


def test_metrics_contract() -> None:
    rendered = DecisionIntelligencePlatform().metrics.render_prometheus()
    for metric in (
        "decisions_total",
        "decision_evaluations_total",
        "decision_recommendations_total",
        "decision_approvals_total",
        "decision_simulations_total",
        "decision_execution_success_total",
        "decision_latency_seconds",
    ):
        assert metric in rendered
