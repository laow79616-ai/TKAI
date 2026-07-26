from __future__ import annotations

from dataclasses import replace

import pytest

from model_platform import (
    DASHBOARD_SECTIONS,
    METRICS,
    BenchmarkRecord,
    Budget,
    DeploymentKind,
    EvaluationRecord,
    GovernanceRecord,
    HealthStatus,
    ModelDeployment,
    ModelPlatform,
    ModelProfile,
    ModelScope,
    ProviderConfiguration,
    Quota,
    RouteRequest,
    RoutingRule,
    ScalingConfiguration,
    UsageRecord,
)
from model_platform.api import register_model_routes

PERMISSIONS = {
    "models:admin",
    "models:read",
    "models:write",
    "models:approve",
    "models:route",
    "models:deploy",
    "models:evaluate",
    "models:govern",
    "models:invoke",
}


def configured() -> tuple[ModelPlatform, ModelScope]:
    platform = ModelPlatform()
    scope = ModelScope("tenant-a", "workspace-a", "alice")
    platform.security.grant(scope, PERMISSIONS)
    return platform, scope


def model_payload(
    model_id: str = "model-a", provider: str = "provider-a"
) -> dict[str, object]:
    return {
        "id": model_id,
        "name": "Enterprise Model",
        "provider": provider,
        "version": "1.0.0",
        "capabilities": ["chat", "reasoning"],
        "context_window": 128_000,
        "input_types": ["text", "image"],
        "output_types": ["text"],
        "metadata": {"owner": "platform"},
    }


def activate(platform: ModelPlatform, scope: ModelScope, model_id: str) -> None:
    for status in ("registered", "validated", "approved", "active"):
        platform.transition(model_id, status, scope)


def test_registry_lifecycle_validation_and_isolation() -> None:
    platform, scope = configured()
    model = platform.register_model(model_payload(), scope)
    assert model.context_window == 128_000
    activate(platform, scope, model.id)
    assert platform.get_model(model.id, scope).status.value == "active"
    with pytest.raises(ValueError):
        platform.transition(model.id, "registered", scope)
    other = ModelScope("tenant-b", "workspace-a", "alice")
    platform.security.grant(other, PERMISSIONS)
    with pytest.raises(PermissionError):
        platform.get_model(model.id, other)


def test_providers_profiles_routing_governance_and_allowlists() -> None:
    platform, scope = configured()
    provider = ProviderConfiguration(
        "provider-a", "openai", "vault://models/openai", "https://example.invalid"
    )
    platform.add_provider(provider, scope)
    model = platform.register_model(model_payload(), scope)
    activate(platform, scope, model.id)
    profile = ModelProfile(
        "default",
        "Default",
        scope.tenant,
        scope.workspace,
        model.id,
        temperature=0.2,
        capabilities=("chat",),
        use_cases=("support",),
    )
    platform.add_profile(profile, scope)
    platform.security.provider_allowlist[(scope.tenant, scope.workspace)] = {
        provider.id
    }
    platform.security.model_allowlist[(scope.tenant, scope.workspace)] = {model.id}
    governance = GovernanceRecord(
        model.id,
        scope.tenant,
        scope.workspace,
        "approved",
        ("support",),
        ("autonomous-trading",),
        "medium",
        "eval-a",
        ("support-policy",),
    )
    platform.set_governance(governance, scope)
    rule = RoutingRule(
        "route-a",
        1,
        model.id,
        provider.id,
        "chat",
        scope.tenant,
        scope.workspace,
        max_cost=0.02,
        max_latency_seconds=2,
        policy="support-policy",
    )
    platform.add_route(rule, scope)
    selected = platform.route(
        RouteRequest(
            scope.tenant,
            scope.workspace,
            "chat",
            "support",
            max_estimated_cost=0.03,
            max_latency_seconds=3,
        ),
        scope,
    )
    assert selected.id == model.id
    with pytest.raises(ValueError, match="credentials"):
        ProviderConfiguration("bad", "custom", metadata={"api_key": "do-not-store"})


class FailingProvider:
    def invoke(self, model: object, request: dict[str, object]) -> dict[str, object]:
        raise TimeoutError("provider timeout")

    def health(self) -> HealthStatus:
        return HealthStatus.UNHEALTHY


class SuccessfulProvider:
    def invoke(self, model: object, request: dict[str, object]) -> dict[str, object]:
        return {
            "output": "ok",
            "input_tokens": 3,
            "output_tokens": 2,
            "estimated_cost": 0.01,
        }

    def health(self) -> HealthStatus:
        return HealthStatus.HEALTHY


def test_ordered_bounded_fallback_usage_cost_quota_and_metrics() -> None:
    platform, scope = configured()
    for provider_id, adapter in (
        ("provider-a", FailingProvider()),
        ("provider-b", SuccessfulProvider()),
    ):
        platform.add_provider(
            ProviderConfiguration(provider_id, "custom", f"vault://{provider_id}"),
            scope,
        )
        platform.bind_provider(provider_id, adapter)
    for model_id, provider_id in (
        ("model-a", "provider-a"),
        ("model-b", "provider-b"),
    ):
        platform.register_model(model_payload(model_id, provider_id), scope)
        activate(platform, scope, model_id)
    platform.add_profile(
        ModelProfile(
            "default",
            "Default",
            scope.tenant,
            scope.workspace,
            "model-a",
            ("model-b",),
            retries=1,
        ),
        scope,
    )
    platform.set_quota(Quota(scope.tenant, scope.workspace, 2, 20, 1, 2), scope)
    response = platform.invoke("default", {"max_tokens": 10}, scope)
    assert response["output"] == "ok"
    assert platform.metrics.snapshot()["model_fallback_total"] == 1
    assert platform.metrics.snapshot()["model_tokens_total"] == 5
    platform.set_budget(Budget(scope.tenant, scope.workspace, 0.01, (0.5, 1.0)), scope)
    assert platform.budget_status(scope)["alerts"] == (0.5, 1.0)
    with pytest.raises(PermissionError, match="quota"):
        platform.check_quota(scope, 16)


def test_deployment_evaluation_benchmarks_and_usage_interfaces() -> None:
    platform, scope = configured()
    platform.register_model(model_payload(), scope)
    deployment = ModelDeployment(
        "deploy-a",
        "model-a",
        scope.tenant,
        scope.workspace,
        DeploymentKind.KUBERNETES,
        "deployment/model-a",
        ScalingConfiguration(1, 5, 10),
    )
    platform.add_deployment(deployment, scope)
    assert (
        platform.set_deployment_health("deploy-a", HealthStatus.HEALTHY, scope).health
        is HealthStatus.HEALTHY
    )
    evaluation = EvaluationRecord(
        "eval-a", "model-a", scope.tenant, scope.workspace, 0.8, 1.0, 0.99, 0.02
    )
    platform.add_evaluation(evaluation, scope)
    platform.add_evaluation(replace(evaluation, id="eval-b", quality=0.9), scope)
    assert platform.compare_evaluations("eval-a", "eval-b")["quality"] == pytest.approx(
        0.1
    )
    benchmark = BenchmarkRecord(
        "bench-a",
        "model-a",
        scope.tenant,
        scope.workspace,
        "dataset://support",
        "support",
        0.8,
        1.0,
        100,
        0.02,
        "1.0.0",
    )
    platform.add_benchmark(benchmark, scope)
    platform.add_benchmark(replace(benchmark, id="bench-b", score=0.9), scope)
    assert platform.compare_versions("bench-a", "bench-b")["score"] == pytest.approx(
        0.1
    )
    platform.record_usage(
        UsageRecord(
            "usage-a",
            "model-a",
            "provider-a",
            scope.tenant,
            scope.workspace,
            10,
            5,
            0.4,
        ),
        scope,
    )


class App:
    def __init__(self) -> None:
        self.routes: set[tuple[str, str]] = set()

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.update((method, path) for method in methods)


def test_api_dashboard_metrics_audit_and_regression_contract() -> None:
    platform, scope = configured()
    app = App()
    register_model_routes(app, platform)
    for path in (
        "/models",
        "/model-providers",
        "/model-profiles",
        "/model-deployments",
        "/model-routing",
        "/model-fallback",
        "/model-evaluations",
        "/model-benchmarks",
        "/model-usage",
        "/model-cost",
        "/model-governance",
    ):
        assert any(route[1] == path for route in app.routes)
    platform.register_model(model_payload(), scope)
    assert platform.dashboard(scope)["sections"] == DASHBOARD_SECTIONS
    assert set(platform.metrics.snapshot()) == set(METRICS)
    platform.security.audit_events.clear()
    from model_platform import AuditEvent

    platform.security.audit(
        AuditEvent(
            "test",
            "model-a",
            scope.tenant,
            scope.workspace,
            scope.actor,
            "success",
            {"token": "secret", "request_id": "safe"},
        )
    )
    assert platform.security.audit_events[-1].metadata == {"request_id": "safe"}
