"""Offline tests for the V8 Hyper Intelligence Fabric."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_intelligence.aggregation import MetadataAggregator
from tkai.v8.hyper_intelligence.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_intelligence.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    HyperIntelligenceProfile,
    IntelligenceReference,
    IntelligenceScope,
    KnowledgeRecord,
    ReasoningSummary,
    Recommendation,
    SignalRecord,
)
from tkai.v8.hyper_intelligence.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v8.hyper_intelligence.fabric import HyperIntelligenceFabric
from tkai.v8.hyper_intelligence.governance import authorizes_execution
from tkai.v8.hyper_intelligence.relationships import Relationship
from tkai.v8.hyper_intelligence.security import (
    IntelligenceAccessController,
    IntelligencePrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def get(self, path: str, **kwargs: object):  # type: ignore[no-untyped-def]
        def decorator(handler: object) -> object:
            self.routes[path] = ("GET", handler)
            return handler

        return decorator


def reference(
    identifier: str, generation: str = "v8"
) -> IntelligenceReference:
    return IntelligenceReference(identifier, "1.0", generation=generation)


def profile() -> HyperIntelligenceProfile:
    return HyperIntelligenceProfile(
        "profile-1",
        "8.0.0",
        "platform",
        framework_references=(reference("framework"),),
        ai_center_references=(reference("center", "v6"),),
        knowledge_references=(reference("knowledge"),),
        evidence_references=(reference("evidence"),),
        signal_references=(reference("signal"),),
        compatibility_references=(reference("compatibility"),),
        health="healthy",
        metrics={"coverage": 1},
        audit=({"event": "created"},),
        metadata={"mode": "reference-only"},
    )


def test_profile_is_complete_immutable_and_never_authorizes_execution() -> None:
    value = profile()
    assert value.profile_id == "profile-1"
    assert value.ai_center_references[0].generation == "v6"
    assert value.execution_authorized is False
    with pytest.raises(TypeError):
        value.metadata["mode"] = "execute"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        value.owner = "other"  # type: ignore[misc]


def test_aggregation_covers_v6_v7_v8_by_reference_only() -> None:
    aggregator = MetadataAggregator()
    result = aggregator.aggregate_all(
        v6_ai_centers=({"identifier": "v6-center"},),
        v7_frameworks=({"identifier": "v7-framework"},),
        v8_frameworks=({"identifier": "v8-framework"},),
    )
    assert {items[0].generation for items in result.values()} == {"v6", "v7", "v8"}
    assert aggregator.executes_actions() is False
    assert aggregator.mutates_runtime_state() is False


def test_knowledge_evidence_relationship_and_context_linkage() -> None:
    fabric = HyperIntelligenceFabric()
    evidence = EvidenceRecord("evidence-1", reference("mock-source"))
    knowledge = KnowledgeRecord(
        "knowledge-1",
        "Mock knowledge",
        "fact",
        evidence_references=(reference("evidence-1"),),
        context_references=(reference("context-1"),),
        relationship_references=(reference("relationship-1"),),
    )
    fabric.register_evidence(evidence)
    fabric.register_knowledge(knowledge)
    fabric.add_relationship(Relationship("knowledge-1", "evidence-1", "supported_by"))
    snapshot = fabric.snapshot()
    assert snapshot["knowledge"][0]["evidence_references"][0]["identifier"] == (
        "evidence-1"
    )
    assert snapshot["relationships"][0]["kind"] == "supported_by"


def test_safe_reasoning_summary_rejects_hidden_reasoning() -> None:
    with pytest.raises(ValueError, match="hidden reasoning"):
        ReasoningSummary(
            "reasoning-1",
            "Safe summary",
            metadata={"chain_of_thought": "must-not-store"},
        )
    summary = ReasoningSummary(
        "reasoning-2",
        "Evidence supports the advisory recommendation.",
        evidence_references=(reference("evidence-1"),),
        confidence=0.8,
        evaluation_references=(reference("evaluation-1"),),
        explanation_references=(reference("explanation-1"),),
    )
    assert summary.confidence == 0.8


def test_recommendations_are_advisory_reference_only_and_non_executing() -> None:
    value = Recommendation(
        "recommendation-1",
        "Review metadata coverage.",
        evidence_references=(reference("evidence-1"),),
        reasoning_reference=reference("reasoning-1"),
        confidence=0.75,
    )
    assert value.advisory is True
    assert value.execution_authorized is False
    assert authorizes_execution(value) is False


def test_cross_version_compatibility_metadata() -> None:
    record = CompatibilityRecord(
        "compatibility-1",
        reference("v6-center", "v6"),
        reference("v8-fabric", "v8"),
    )
    fabric = HyperIntelligenceFabric()
    fabric.register_compatibility(record)
    assert fabric.snapshot()["compatibility"][0]["status"] == "compatible"


def test_security_isolation_secret_filtering_observability_and_audit() -> None:
    fabric = HyperIntelligenceFabric(
        metadata={"api_key": "secret", "visible": "safe"}
    )
    controller = IntelligenceAccessController()
    principal = IntelligencePrincipal(
        "reader",
        tenant="tenant-a",
        workspace="workspace-a",
        knowledge_namespaces=frozenset({"knowledge-a"}),
    )
    scope = IntelligenceScope("tenant-a", "workspace-a", "knowledge-a")
    controller.authorize(principal, "intelligence:read", scope)
    with pytest.raises(PermissionError, match="tenant isolation"):
        controller.authorize(
            principal,
            "intelligence:read",
            IntelligenceScope("tenant-b", "workspace-a", "knowledge-a"),
        )
    with pytest.raises(PermissionError, match="knowledge isolation"):
        controller.authorize(
            principal,
            "intelligence:read",
            IntelligenceScope("tenant-a", "workspace-a", "knowledge-b"),
        )
    assert fabric.metadata["api_key"] == "[REDACTED]"
    fabric.observability.trace("mock-read", "correlation-1")
    assert fabric.snapshot()["traces"]
    assert fabric.snapshot()["audit"]


def test_health_metrics_dashboard_and_get_only_api() -> None:
    fabric = HyperIntelligenceFabric()
    fabric.register_profile(profile())
    fabric.register_signal(
        SignalRecord("signal-1", "mock", reference("mock-source"))
    )
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["sections"] == DASHBOARD_SECTIONS
    assert set(DASHBOARD_SECTIONS) == {
        "Hyper Intelligence Overview",
        "Knowledge",
        "Evidence",
        "Signals",
        "Recommendations",
        "Compatibility",
        "Health",
        "Metrics",
        "Audit",
    }
    assert fabric.health()["status"] == "healthy"
    assert fabric.metrics()["profiles"] == 1
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.approves_execution() is False

    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operation) == {"get"}
        for operation in openapi_contract()["paths"].values()  # type: ignore[union-attr]
    )


def test_existing_v6_v7_v8_imports_remain_available() -> None:
    from tkai.v7.intelligence_framework import IntelligenceFramework
    from tkai.v8.hyper_coordination import HyperCoordinationFramework
    from tkai.v8.kernel import HyperKernel

    assert IntelligenceFramework is not None
    assert HyperCoordinationFramework().overview()["execution"] == "disabled"
    assert HyperKernel().overview()["execution"] == "disabled"
