"""Offline tests for bounded advisory intelligence behavior."""
import importlib
from datetime import datetime, timezone

import pytest

from tkai.v7.intelligence_framework import (
    Approval,
    DecisionRecord,
    Evidence,
    IntelligenceContext,
    IntelligenceFramework,
    IntelligenceFrameworkError,
    IntelligenceProfile,
    Lifecycle,
    Observation,
    Recommendation,
    Scope,
    SourceAdapter,
    safe_metadata,
)
from tkai.v7.intelligence_framework.api import (
    INTELLIGENCE_ENDPOINTS,
    register_intelligence_framework_routes,
)

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)
SCOPE = Scope("tenant-a", "workspace-a", "intel")


def profile(scope: Scope = SCOPE) -> IntelligenceProfile:
    return IntelligenceProfile("p1", "profile", "description", "owner", scope,
                               "30-days")


def decision(**changes: object) -> DecisionRecord:
    values = {
        "decision_id": "d1", "profile_reference": "p1",
        "context_reference": "c1", "decision_type": "selection",
        "objective_references": (), "evidence_references": (),
        "knowledge_references": (), "alternative_references": (),
        "constraint_references": (), "policy_references": (),
        "risk_references": (), "recommendation_references": (),
        "confidence": .5, "status": "advisory", "scope": SCOPE,
    }
    values.update(changes)
    return DecisionRecord(**values)  # type: ignore[arg-type]


def test_required_package_structure() -> None:
    names = (
        "profiles contexts sources evidence knowledge signals observations reasoning "
        "hypotheses evaluations decisions alternatives comparisons confidence "
        "recommendations explanations reviews approvals governance policies history "
        "versions analytics health metrics audit security events contracts interfaces "
        "lifecycle dashboard api"
    ).split()
    for name in names:
        importlib.import_module(f"tkai.v7.intelligence_framework.{name}")


def test_profiles_contexts_lifecycle_and_scope_isolation() -> None:
    framework = IntelligenceFramework()
    framework.register_profile(profile())
    context = IntelligenceContext("c1", "p1", "subject", "ref://subject",
                                  (NOW, NOW), SCOPE)
    framework.create_context(context)
    assert framework.transition("p1", Lifecycle.READY, SCOPE).version == 2
    with pytest.raises(IntelligenceFrameworkError):
        framework.create_context(
            IntelligenceContext("cross", "p1", "subject", "ref://subject",
                                (NOW, NOW), Scope("other", "workspace-a", "intel"))
        )


def test_sources_are_bounded_read_only_and_local() -> None:
    framework = IntelligenceFramework()
    sources = framework.projection("sources", SCOPE)
    assert len(sources) == 23  # type: ignore[arg-type]
    assert all(x["read_only"] and x["local_only"] for x in sources)  # type: ignore[union-attr]
    with pytest.raises(ValueError):
        SourceAdapter("unsafe", "unsafe", "1", read_only=False)


def test_evidence_is_reference_only_and_secret_safe() -> None:
    framework = IntelligenceFramework()
    evidence = Evidence("e1", "metric", "v7-data-storage-framework",
                        "ref://subject", (NOW, NOW), "data://records/1", "a" * 64,
                        "valid", .8, .9, .7, "local", "validated", SCOPE)
    framework.record_evidence(evidence)
    assert framework.metrics["v7_intelligence_evidence_validated_total"] == 1
    with pytest.raises(ValueError):
        Evidence("e2", "metric", "source", "subject", (NOW, NOW), "plaintext",
                 "a" * 64, "valid", .8, .9, .7, "local", "validated", SCOPE)
    with pytest.raises(ValueError):
        safe_metadata({"api_key": "plaintext"})


def test_observations_decisions_recommendations_and_approvals_are_safe() -> None:
    with pytest.raises(ValueError):
        Observation("o1", "c1", (), (), "claim", "observation", .5,
                    "unverified", NOW, SCOPE, is_fact=True)
    with pytest.raises(ValueError):
        decision(execution_authorized=True)
    with pytest.raises(ValueError):
        Recommendation("r1", "decision-selection", "d1", "consider A", (), .5,
                       SCOPE, executable=True)
    with pytest.raises(ValueError):
        Approval("a1", "d1", 1, "artifact", "reviewer", "approved", (), None,
                 NOW, SCOPE, execution_authorized=True)


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(self, path: str, _handler: object, *,
                      methods: list[str], tags: list[str]) -> None:
        self.routes.append((path, tuple(methods)))


def test_api_is_complete_get_only_and_has_no_dangerous_endpoint() -> None:
    app = FakeApp()
    register_intelligence_framework_routes(app, IntelligenceFramework())
    assert {path for path, _ in app.routes} == {
        f"/v7/intelligence/{name}" for name in INTELLIGENCE_ENDPOINTS
    }
    assert all(methods == ("GET",) for _, methods in app.routes)
    blocked = ("execute", "approve", "mutate", "chain-of-thought",
               "hidden-reasoning", "secret")
    assert not any(word in path for path, _ in app.routes for word in blocked)
