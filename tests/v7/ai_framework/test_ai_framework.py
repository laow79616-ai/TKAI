import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from tkai.v7.ai_framework import (
    AIFrameworkError,
    AIModel,
    ContextLimits,
    Evaluation,
    GovernanceRecord,
    Lifecycle,
    PromptTemplate,
    ProviderDefinition,
    ProviderKind,
    ReasoningSession,
    ReviewStatus,
    RiskClass,
    RouteRequest,
    SafetyPolicy,
    Scope,
    UnifiedAIFramework,
)
from tkai.v7.ai_framework.api import AI_ENDPOINTS, register_ai_framework_routes
from tkai.v7.ai_framework.dashboard import DASHBOARD_SECTIONS, AIDashboard


def populated() -> tuple[UnifiedAIFramework, Scope]:
    framework = UnifiedAIFramework()
    scope = Scope("tenant-a", "workspace-a")
    framework.register_provider(
        ProviderDefinition("mock", ProviderKind.MOCK, scope, "Mock")
    )
    framework.register_template(
        PromptTemplate("summary", "1.0.0", scope, "Summarize {content}", ("content",))
    )
    framework.register_safety_policy(
        SafetyPolicy(
            "safe-default",
            scope,
            ("content://default",),
            RiskClass.LOW,
            ReviewStatus.APPROVED,
        )
    )
    framework.register_model(
        AIModel(
            "model-a",
            "mock",
            "Mock A",
            "1.0.0",
            scope,
            frozenset({"summarize"}),
            ContextLimits(4096, 512),
            prompt_template_references=("summary:1.0.0",),
            safety_policy_references=("safe-default",),
            lifecycle=Lifecycle.ACTIVE,
        )
    )
    framework.register_evaluation(Evaluation("eval-a", scope, "model-a", 0.9, 10, 1, 1))
    framework.register_governance(
        GovernanceRecord(
            "approval-a",
            scope,
            "model-a",
            ReviewStatus.APPROVED,
            safety_references=("safe-default",),
        )
    )
    return framework, scope


def test_provider_kinds_registry_and_secret_references() -> None:
    assert {kind.value for kind in ProviderKind} == {
        "local",
        "openai-compatible",
        "generic-http",
        "mock",
        "test",
    }
    framework, scope = populated()
    assert framework.projection("providers", scope)[0]["provider_id"] == "mock"
    with pytest.raises(ValueError):
        ProviderDefinition(
            "unsafe",
            ProviderKind.GENERIC_HTTP,
            scope,
            "Unsafe",
            secret_references=("plain-text-key",),
        )


def test_template_validation_and_reasoning_privacy() -> None:
    framework, scope = populated()
    with pytest.raises(AIFrameworkError):
        framework.register_template(
            PromptTemplate("bad", "1.0.0", scope, "Static", ("missing",))
        )
    with pytest.raises(ValueError):
        ReasoningSession(
            "session-a",
            scope,
            "model-a",
            metadata={"chain_of_thought": "must not persist"},
        )


def test_metadata_routing_evaluation_governance_and_fallback() -> None:
    framework, scope = populated()
    decision = framework.route(RouteRequest(scope, frozenset({"summarize"})))
    assert decision.model_id == "model-a"
    assert decision.executable is False
    assert framework.metrics["v7_ai_route_decisions_total"] == 1


def test_scope_isolation_health_metrics_and_audit() -> None:
    framework, scope = populated()
    other = Scope("tenant-b", "workspace-a")
    assert framework.projection("models", other) == []
    assert framework.health(scope)["external_calls_enabled"] is False
    assert framework.projection("metrics", scope)
    assert framework.projection("audit", scope)
    for forbidden in ("execute", "invoke", "complete", "chat", "tiktok"):
        assert not hasattr(framework, forbidden)


def test_dashboard_and_get_only_api_openapi() -> None:
    framework, scope = populated()
    snapshot = AIDashboard(framework).snapshot(scope)
    assert set(snapshot) == set(DASHBOARD_SECTIONS)
    app = FastAPI()
    register_ai_framework_routes(app, framework)
    client = TestClient(app)
    params = {"tenant": "tenant-a", "workspace": "workspace-a"}
    for endpoint in AI_ENDPOINTS:
        path = f"/v7/ai/{endpoint}"
        assert client.get(path, params=params).status_code == 200
        assert client.post(path, params=params).status_code == 405
        assert set(app.openapi()["paths"][path]) == {"get"}


def test_v6_and_existing_v7_imports_remain_available() -> None:
    import tkai
    import tkai.plugins
    import tkai.v7.extension_framework

    assert tkai and tkai.plugins and tkai.v7.extension_framework
