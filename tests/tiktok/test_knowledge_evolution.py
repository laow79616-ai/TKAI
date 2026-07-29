"""Offline tests for the Enterprise TikTok Knowledge Evolution Center."""

import pytest

from tiktok.knowledge_evolution import (
    KnowledgeContext,
    KnowledgeProfile,
    TikTokKnowledgeEvolutionCenter,
)
from tiktok.knowledge_evolution.adapters import (
    KNOWLEDGE_SOURCES,
    ReferenceOnlyKnowledgePort,
)
from tiktok.knowledge_evolution.api import (
    ROUTES,
    register_knowledge_evolution_routes,
)
from tiktok.knowledge_evolution.metrics import METRIC_NAMES


def context(workspace: str = "workspace") -> KnowledgeContext:
    return KnowledgeContext(
        "tenant",
        workspace,
        "curator",
        frozenset({"tiktok:knowledge:admin"}),
    )


def profile(workspace: str = "workspace") -> KnowledgeProfile:
    return KnowledgeProfile(
        "profile",
        "Operational Knowledge",
        "Read-only knowledge refinement.",
        "tenant",
        workspace,
        "curator",
        KNOWLEDGE_SOURCES,
    )


def test_knowledge_aggregation_is_bounded_explainable_and_offline() -> None:
    service = TikTokKnowledgeEvolutionCenter()
    service.create_profile(profile(), context())
    evidence = service.aggregate("profile", "retention", context())
    assert len(evidence) == len(KNOWLEDGE_SOURCES)
    assert all(item.integrity_reference and item.summary for item in evidence)
    adapter = ReferenceOnlyKnowledgePort("learning_center")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "publish")
    assert not hasattr(adapter, "configure")


def test_evolution_versioning_comparison_and_confidence() -> None:
    service = TikTokKnowledgeEvolutionCenter()
    service.create_profile(profile(), context())
    first = service.evolve(
        "v1", "profile", "retention", "Initial knowledge.", context()
    )
    second = service.evolve(
        "v2", "profile", "retention", "Refined knowledge.", context()
    )
    comparison = service.compare("comparison", "v1", "v2", context())
    assert (first.number, second.number) == (1, 2)
    assert second.previous_version_id == first.id
    assert comparison.summary_changed
    assert comparison.confidence_delta == 0
    assert second.explanation
    assert 0 <= second.confidence <= 1


def test_recommendations_are_advisory_and_never_execute() -> None:
    service = TikTokKnowledgeEvolutionCenter()
    service.create_profile(profile(), context())
    service.evolve("v1", "profile", "retention", "Knowledge.", context())
    recommendation = service.recommend(
        "r1",
        "v1",
        "Review the retention hypothesis",
        "The evidence is stable but warrants human review.",
        context(),
        confidence=0.7,
    )
    assert recommendation.advisory_only
    assert recommendation.direct_execution is False
    assert recommendation.evidence_references


def test_analytics_security_audit_and_secret_protection() -> None:
    service = TikTokKnowledgeEvolutionCenter()
    service.create_profile(profile(), context())
    service.evolve("v1", "profile", "subject", "Summary.", context())
    assert service.analytics(context())["average_confidence"] == 0.75
    assert service.audit
    with pytest.raises(PermissionError):
        service.aggregate("profile", "subject", context("other"))
    with pytest.raises(PermissionError, match="RBAC"):
        service.analytics(KnowledgeContext("tenant", "workspace", "guest", frozenset()))
    unsafe = profile()
    unsafe.id = "unsafe"
    unsafe.metadata = {"token": "forbidden"}
    with pytest.raises(ValueError, match="Secrets"):
        service.create_profile(unsafe, context())


def test_api_dashboard_metrics_and_read_only_contract() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str]]] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.routes.append((path, list(kwargs["methods"])))

    service = TikTokKnowledgeEvolutionCenter()
    service.create_profile(profile(), context())
    dashboard = service.dashboard(context())
    assert dashboard["sections"] == [
        "knowledge_overview",
        "knowledge_sources",
        "knowledge_versions",
        "evolution_timeline",
        "recommendations",
        "analytics",
        "history",
    ]
    assert dashboard["knowledge_overview"] == {
        "read_only": True,
        "direct_execution": False,
        "runtime_configuration_mutation": False,
        "publishing": False,
        "restriction_bypass": False,
    }
    assert set(dashboard["knowledge_sources"]) == set(KNOWLEDGE_SOURCES)
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    app = App()
    register_knowledge_evolution_routes(app, service)
    assert set(ROUTES).issubset(path for path, _ in app.routes)
    assert all(methods == ["GET"] for _, methods in app.routes)
