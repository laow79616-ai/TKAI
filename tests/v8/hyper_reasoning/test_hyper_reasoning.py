"""Mock-only coverage for the V8 Hyper Reasoning Fabric."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_reasoning.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_reasoning.contracts import (
    CompatibilityRecord,
    ConfidenceMetadata,
    EvaluationMetadata,
    EvidenceRecord,
    ExplanationSummary,
    KnowledgeReferenceRecord,
    ReasoningMetadata,
    ReasoningProfile,
    ReasoningReference,
    ReasoningScope,
    Recommendation,
)
from tkai.v8.hyper_reasoning.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v8.hyper_reasoning.evidence import EvidenceAggregator
from tkai.v8.hyper_reasoning.fabric import HyperReasoningFabric
from tkai.v8.hyper_reasoning.security import (
    ReasoningAccessController,
    ReasoningPrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self,
        path: str,
        handler: object,
        *,
        methods: list[str],
        tags: list[str],
    ) -> None:
        assert tags == ["V8 Hyper Reasoning"]
        self.routes[path] = (methods[0], handler)


def reference(identifier: str, generation: str = "v8") -> ReasoningReference:
    return ReasoningReference(identifier, "1.0.0", generation=generation)


def test_reasoning_profile_is_complete_immutable_and_reference_only() -> None:
    profile = ReasoningProfile(
        "profile-1",
        "8.0.0",
        "reasoning-team",
        context_references=(reference("context-1"),),
        evidence_references=(reference("evidence-1"),),
        knowledge_references=(reference("knowledge-1"),),
        reasoning_references=(reference("reasoning-1"),),
        evaluation_references=(reference("evaluation-1"),),
        recommendation_references=(reference("recommendation-1"),),
        compatibility_references=(reference("compatibility-1"),),
        governance_references=(reference("policy-1"),),
        health="healthy",
        metrics={"coverage": 1.0},
        audit=({"event": "mock-created"},),
        metadata={"classification": "internal"},
    )
    fabric = HyperReasoningFabric()
    fabric.register_profile(profile)
    serialized = fabric.snapshot()["profiles"][0]
    assert serialized["owner"] == "reasoning-team"
    assert serialized["execution_authorized"] is False
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_safe_reasoning_metadata_links_evidence_evaluation_and_confidence() -> None:
    item = ReasoningMetadata(
        "reasoning-1",
        "Evidence supports further review.",
        evidence_references=(reference("evidence-1"),),
        evaluation_references=(reference("evaluation-1"),),
        confidence_reference=reference("confidence-1"),
        decision_references=(reference("decision-1"),),
        governance_references=(reference("policy-1"),),
    )
    fabric = HyperReasoningFabric()
    fabric.register_reasoning(item)
    assert fabric.snapshot()["reasoning"][0]["summary"] == item.summary
    assert fabric.diagnostics()[0]["code"] == "unresolved-evidence-reference"
    for forbidden in (
        {"chain_of_thought": "never"},
        {"nested": {"hidden_reasoning": "never"}},
    ):
        with pytest.raises(ValueError, match="chain-of-thought"):
            ReasoningMetadata("unsafe", "Safe summary", metadata=forbidden)


def test_evidence_aggregation_covers_required_v6_v7_v8_sources() -> None:
    aggregator = EvidenceAggregator()
    sources = aggregator.aggregate(
        v8_hyper_knowledge=({"identifier": "hyper-knowledge"},),
        v8_hyper_intelligence=({"identifier": "hyper-intelligence"},),
        v8_frameworks=({"identifier": "v8-framework"},),
        v7_frameworks=({"identifier": "v7-framework"},),
        v6_ai_centers=({"identifier": "v6-center"},),
    )
    assert set(sources) == set(EvidenceAggregator.SOURCE_NAMES)
    assert {items[0].generation for items in sources.values()} == {
        "v6",
        "v7",
        "v8",
    }
    assert aggregator.executes_actions() is False
    assert aggregator.mutates_runtime_state() is False


def test_evidence_confidence_and_evaluation_metadata() -> None:
    fabric = HyperReasoningFabric()
    fabric.register_evidence(
        EvidenceRecord(
            "evidence-1",
            reference("mock-source"),
            provenance={"fixture": "mock"},
            reliability=0.9,
        )
    )
    fabric.register_evaluation(
        EvaluationMetadata(
            "evaluation-1",
            reference("reasoning-1"),
            outcome="supported",
            evidence_references=(reference("evidence-1"),),
        )
    )
    fabric.register_confidence(
        ConfidenceMetadata(
            "confidence-1",
            0.8,
            calibration_metadata={"method": "mock-calibration"},
            evidence_coverage=0.75,
            reliability_metadata={"rating": "high"},
            limitations=("Mock inputs only.",),
            version_history=({"version": "1.0.0"},),
        )
    )
    snapshot = fabric.snapshot()
    assert snapshot["evidence"][0]["reliability"] == 0.9
    assert snapshot["confidence"][0]["evidence_coverage"] == 0.75
    with pytest.raises(ValueError, match="between 0 and 1"):
        ConfidenceMetadata("invalid", 1.1)


def test_explanations_are_safe_and_recommendations_are_advisory() -> None:
    explanation = ExplanationSummary(
        "explanation-1",
        "The recommendation is supported by the referenced fixture.",
        evidence_references=(reference("evidence-1"),),
        assumption_references=(reference("assumption-1"),),
        limitation_summaries=("Fixture coverage is limited.",),
        policy_references=(reference("policy-1"),),
    )
    recommendation = Recommendation(
        "recommendation-1",
        "Review evidence coverage.",
        reasoning_references=(reference("reasoning-1"),),
        evidence_references=(reference("evidence-1"),),
        confidence_reference=reference("confidence-1"),
        decision_references=(reference("decision-1"),),
    )
    fabric = HyperReasoningFabric()
    fabric.register_explanation(explanation)
    fabric.register_recommendation(recommendation)
    assert fabric.snapshot()["recommendations"][0]["advisory"] is True
    assert recommendation.execution_authorized is False
    assert fabric.exposes_chain_of_thought() is False


def test_knowledge_compatibility_and_backward_compatible_imports() -> None:
    fabric = HyperReasoningFabric()
    fabric.register_knowledge(
        KnowledgeReferenceRecord(
            "knowledge-1",
            reference("v8-hyper-knowledge"),
            evidence_references=(reference("evidence-1"),),
        )
    )
    fabric.register_compatibility(
        CompatibilityRecord(
            "compatibility-1",
            reference("v6-center", "v6"),
            reference("v8-reasoning", "v8"),
        )
    )
    from tkai.v7.intelligence_framework import IntelligenceFramework
    from tkai.v8.hyper_intelligence import HyperIntelligenceFabric
    from tkai.v8.hyper_knowledge import HyperKnowledgeFabric

    assert fabric.metrics()["compatibility"] == 1
    assert IntelligenceFramework is not None
    assert HyperKnowledgeFabric is not None
    assert HyperIntelligenceFabric is not None


def test_security_isolation_secret_filtering_observability_and_audit() -> None:
    fabric = HyperReasoningFabric(
        metadata={"api_key": "mock-secret", "visible": "safe"}
    )
    controller = ReasoningAccessController()
    principal = ReasoningPrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
        reasoning_namespaces=frozenset({"domain-a"}),
    )
    scope = ReasoningScope("tenant-a", "workspace-a", "domain-a")
    controller.authorize(principal, "reasoning:read", scope)
    for invalid in (
        ReasoningScope("tenant-b", "workspace-a", "domain-a"),
        ReasoningScope("tenant-a", "workspace-b", "domain-a"),
        ReasoningScope("tenant-a", "workspace-a", "domain-b"),
    ):
        with pytest.raises(PermissionError):
            controller.authorize(principal, "reasoning:read", invalid)
    assert fabric.metadata["api_key"] == "[REDACTED]"
    fabric.observability.log("info", "mock log", {"token": "hidden"})
    fabric.observability.trace("reasoning-read", "mock-correlation")
    snapshot = fabric.snapshot()
    assert snapshot["logs"][0]["metadata"]["token"] == "[REDACTED]"
    assert snapshot["traces"]
    assert snapshot["audit"]


def test_dashboard_health_metrics_api_and_execution_guards() -> None:
    fabric = HyperReasoningFabric()
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["read_only"] is True
    assert set(DASHBOARD_SECTIONS) == {
        "Reasoning Overview",
        "Evidence",
        "Knowledge",
        "Confidence",
        "Recommendations",
        "Explainability",
        "Compatibility",
        "Health",
        "Metrics",
        "Audit",
    }
    assert fabric.health()["status"] == "healthy"
    assert fabric.metrics()["profiles"] == 0
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.authorizes_execution() is False

    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert set(paths) == set(GET_ROUTES)
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert all("chain" not in path and "thought" not in path for path in GET_ROUTES)
