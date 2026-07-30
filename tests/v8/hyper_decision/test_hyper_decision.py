"""Mock-only tests for the V8 Hyper Decision Fabric."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_decision.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_decision.contracts import (
    AlternativeMetadata,
    ApprovalMetadata,
    ComparisonKind,
    ComparisonMetadata,
    CompatibilityMetadata,
    ConfidenceMetadata,
    DecisionMetadata,
    DecisionProfile,
    DecisionReference,
    DecisionScope,
    RecommendationMetadata,
    ReviewMetadata,
)
from tkai.v8.hyper_decision.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v8.hyper_decision.fabric import HyperDecisionFabric
from tkai.v8.hyper_decision.security import (
    DecisionAccessController,
    DecisionPrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["V8 Hyper Decision"]
        self.routes[path] = (methods[0], handler)


def reference(identifier: str, generation: str = "v8") -> DecisionReference:
    return DecisionReference(identifier, "1.0.0", generation=generation)


def test_decision_profile_is_complete_immutable_and_reference_only() -> None:
    profile = DecisionProfile(
        "profile-1",
        "8.0.0",
        "decision-team",
        decision_references=(reference("decision-1"),),
        alternative_references=(reference("alternative-1"),),
        evidence_references=(reference("evidence-1"),),
        knowledge_references=(reference("knowledge-1"),),
        reasoning_references=(reference("reasoning-1"),),
        recommendation_references=(reference("recommendation-1"),),
        governance_references=(reference("policy-1"),),
        compatibility_references=(reference("compatibility-1"),),
        health="healthy",
        metrics={"coverage": 1.0},
        audit=({"event": "mock-created"},),
        metadata={"classification": "internal"},
    )
    fabric = HyperDecisionFabric()
    fabric.register_profile(profile)
    serialized = fabric.snapshot()["profiles"][0]
    assert serialized["owner"] == "decision-team"
    assert serialized["execution_authorized"] is False
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_decisions_alternatives_comparisons_and_recommendations_are_advisory() -> None:
    fabric = HyperDecisionFabric()
    decision = DecisionMetadata(
        "decision-1",
        "Select an option for human review.",
        "advisory",
        evidence_references=(reference("evidence-1"),),
        recommendation_references=(reference("recommendation-1"),),
        evaluation_references=(reference("evaluation-1"),),
        confidence_reference=reference("confidence-1"),
        review_references=(reference("review-1"),),
        approval_references=(reference("approval-1"),),
        version_history=({"version": "1.0.0"},),
        explainability_summary="Referenced evidence favors alternative A.",
    )
    alternative = AlternativeMetadata(
        "alternative-1",
        "Alternative A",
        expected_outcomes=("Mock outcome.",),
        risk_summaries=("Mock risk.",),
        constraint_references=(reference("constraint-1"),),
        evidence_references=(reference("evidence-1"),),
        comparison_references=(reference("comparison-1"),),
    )
    comparison = ComparisonMetadata(
        "comparison-1",
        ComparisonKind.ALTERNATIVE,
        reference("alternative-1"),
        reference("alternative-2"),
        "A has more evidence.",
    )
    recommendation = RecommendationMetadata(
        "recommendation-1",
        "Review alternative A.",
        decision_references=(reference("decision-1"),),
        alternative_references=(reference("alternative-1"),),
    )
    fabric.register_decision(decision)
    fabric.register_alternative(alternative)
    fabric.register_comparison(comparison)
    fabric.register_recommendation(recommendation)
    snapshot = fabric.snapshot()
    assert snapshot["decisions"][0]["executable"] is False
    assert snapshot["recommendations"][0]["advisory"] is True
    assert recommendation.execution_authorized is False
    assert set(ComparisonKind) == {
        ComparisonKind.DECISION,
        ComparisonKind.ALTERNATIVE,
        ComparisonKind.HISTORICAL,
        ComparisonKind.EVIDENCE,
        ComparisonKind.CONFIDENCE,
        ComparisonKind.GOVERNANCE,
        ComparisonKind.COMPATIBILITY,
    }


def test_reviews_approvals_and_compatibility_never_authorize_execution() -> None:
    fabric = HyperDecisionFabric()
    fabric.register_review(
        ReviewMetadata(
            "review-1",
            reference("decision-1"),
            reviewer_references=(reference("reviewer-1"),),
            findings=("Mock finding.",),
            recommendations=("Seek human review.",),
            audit=({"event": "reviewed"},),
        )
    )
    approval = ApprovalMetadata(
        "approval-1",
        reference("decision-1"),
        approver_references=(reference("approver-1"),),
        status="approved-metadata",
    )
    fabric.register_approval(approval)
    for generation in ("v6", "v7", "v8"):
        fabric.register_compatibility(
            CompatibilityMetadata(
                f"compatibility-{generation}",
                reference(f"{generation}-source", generation),
                reference("v8-decision", "v8"),
            )
        )
    assert approval.authorizes_execution is False
    assert fabric.metrics()["compatibility"] == 3
    from tkai.v7.ai_framework import UnifiedAIFramework
    from tkai.v8.hyper_reasoning import HyperReasoningFabric

    assert UnifiedAIFramework is not None
    assert HyperReasoningFabric is not None


def test_confidence_security_isolation_secret_filtering_and_observability() -> None:
    fabric = HyperDecisionFabric(metadata={"api_key": "mock-secret", "visible": "safe"})
    fabric.register_confidence(
        ConfidenceMetadata("confidence-1", 0.8, 0.75, {"method": "mock"})
    )
    with pytest.raises(ValueError, match="between 0 and 1"):
        ConfidenceMetadata("invalid", 1.1)
    controller = DecisionAccessController()
    principal = DecisionPrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
        decision_namespaces=frozenset({"domain-a"}),
    )
    scope = DecisionScope("tenant-a", "workspace-a", "domain-a")
    controller.authorize(principal, "decision:read", scope)
    for invalid in (
        DecisionScope("tenant-b", "workspace-a", "domain-a"),
        DecisionScope("tenant-a", "workspace-b", "domain-a"),
        DecisionScope("tenant-a", "workspace-a", "domain-b"),
    ):
        with pytest.raises(PermissionError):
            controller.authorize(principal, "decision:read", invalid)
    assert fabric.metadata["api_key"] == "[REDACTED]"
    fabric.observability.log("info", "mock log", {"token": "hidden"})
    fabric.observability.trace("decision-read", "mock-correlation")
    assert fabric.snapshot()["logs"][0]["metadata"]["token"] == "[REDACTED]"
    assert fabric.snapshot()["traces"]
    assert fabric.snapshot()["audit"]


def test_dashboard_health_metrics_api_and_guards() -> None:
    fabric = HyperDecisionFabric()
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["read_only"] is True
    assert set(DASHBOARD_SECTIONS) == {
        "Decision Overview",
        "Alternatives",
        "Comparisons",
        "Recommendations",
        "Reviews",
        "Approvals",
        "Compatibility",
        "Health",
        "Metrics",
        "Audit",
    }
    assert fabric.health()["status"] == "healthy"
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.authorizes_execution() is False
    assert fabric.automatically_approves() is False
    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert set(paths) == set(GET_ROUTES)
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert not any("execute" in path or "automatic" in path for path in GET_ROUTES)


def test_metadata_aggregation_is_reference_only_and_secret_filtered() -> None:
    fabric = HyperDecisionFabric()
    sources = fabric.aggregate_metadata(
        v6_ai_centers=({"id": "v6-ai-center", "token": "hidden"},),
        v7_frameworks=({"id": "v7-framework"},),
        v8_frameworks=({"id": "v8-framework"},),
    )
    assert sources["v6_ai_centers"][0]["token"] == "[REDACTED]"
    assert fabric.metrics()["aggregated_references"] == 3
