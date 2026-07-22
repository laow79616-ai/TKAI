"""Offline regression tests for the provider-neutral cost-aware router."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import timedelta

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    CircuitState,
    ThresholdStrategy,
)
from tkai.commands import ai as ai_commands
from tkai.health import HealthRegistry, HealthSnapshot, HealthStatus
from tkai.routing import (
    ProviderMetadata,
    ProviderMetadataNotFoundError,
    RoutingError,
    RoutingManager,
    RoutingRegistry,
)

runner = CliRunner()


def healthy_registry(*providers: str) -> HealthRegistry:
    """Create passive healthy snapshots without issuing network requests."""
    registry = HealthRegistry()
    for provider in providers:
        registry.update(HealthSnapshot(provider, status=HealthStatus.HEALTHY))
    return registry


def manager_with(
    *metadata: ProviderMetadata,
    health: HealthRegistry | None = None,
    breakers: CircuitBreakerRegistry | None = None,
) -> RoutingManager:
    """Create and populate a standalone routing manager deterministically."""
    manager = RoutingManager(health_registry=health, breaker_registry=breakers)
    for item in metadata:
        manager.register(item)
    return manager


def test_metadata_is_immutable_and_validates_cost_weight() -> None:
    metadata = ProviderMetadata(
        "primary",
        priority=3,
        weight=2,
        prompt_cost_per_1k=0.2,
        completion_cost_per_1k=0.4,
        capabilities=frozenset({"chat"}),
        tags=frozenset({"local"}),
    )

    assert metadata.cost_per_1k == pytest.approx(0.6)
    with pytest.raises(FrozenInstanceError):
        metadata.priority = 0  # type: ignore[misc]
    with pytest.raises(ValueError):
        ProviderMetadata("invalid", weight=0)
    with pytest.raises(ValueError):
        ProviderMetadata("invalid", prompt_cost_per_1k=-1)


def test_registry_is_stable_and_protects_duplicates() -> None:
    registry = RoutingRegistry()
    registry.register(ProviderMetadata("secondary"))
    registry.register(ProviderMetadata("primary"))

    assert [item.provider for item in registry.list()] == ["primary", "secondary"]
    with pytest.raises(RoutingError):
        registry.register(ProviderMetadata("primary"))
    assert registry.remove("primary").provider == "primary"
    with pytest.raises(ProviderMetadataNotFoundError):
        registry.get("primary")
    registry.clear()
    assert registry.list() == []


def test_cost_priority_weight_and_capability_selection_are_deterministic() -> None:
    health = healthy_registry("cheap", "priority", "weight", "tools")
    routing = manager_with(
        ProviderMetadata("cheap", prompt_cost_per_1k=0.1),
        ProviderMetadata("priority", priority=5, prompt_cost_per_1k=1),
        ProviderMetadata("weight", priority=5, weight=3, prompt_cost_per_1k=1),
        ProviderMetadata(
            "tools", prompt_cost_per_1k=2, capabilities=frozenset({"chat", "tools"})
        ),
        health=health,
    )

    assert routing.route().selected_provider == "cheap"
    routing.remove("cheap")
    routing.remove("tools")
    assert routing.route().selected_provider == "weight"
    routing.register(
        ProviderMetadata(
            "tools", prompt_cost_per_1k=2, capabilities=frozenset({"chat", "tools"})
        )
    )
    decision = routing.route(required_capabilities=frozenset({"tools"}))
    assert decision.selected_provider == "tools"


def test_unhealthy_and_open_breaker_candidates_are_filtered() -> None:
    health = healthy_registry("healthy", "unhealthy", "open")
    health.update(HealthSnapshot("unhealthy", status=HealthStatus.UNHEALTHY))
    breakers = CircuitBreakerRegistry()
    open_breaker = CircuitBreaker(
        "open",
        strategy=ThresholdStrategy(
            failure_threshold=1,
            open_duration=timedelta(seconds=30),
            half_open_success_threshold=1,
        ),
    )
    open_breaker.record_failure()
    breakers.register("open", open_breaker)
    routing = manager_with(
        ProviderMetadata("healthy", prompt_cost_per_1k=3),
        ProviderMetadata("unhealthy", prompt_cost_per_1k=0),
        ProviderMetadata("open", prompt_cost_per_1k=0),
        health=health,
        breakers=breakers,
    )

    decision = routing.route()

    assert decision.selected_provider == "healthy"
    assert decision.candidate_providers == ("healthy",)


def test_half_open_candidate_is_allowed_but_penalized_for_equal_cost() -> None:
    health = healthy_registry("half", "closed")
    breakers = CircuitBreakerRegistry()
    half_open = CircuitBreaker(
        "half",
        strategy=ThresholdStrategy(
            failure_threshold=1,
            open_duration=timedelta(seconds=0),
            half_open_success_threshold=1,
        ),
    )
    half_open.record_failure()
    assert half_open.allow_request()
    assert half_open.snapshot.state is CircuitState.HALF_OPEN
    breakers.register("half", half_open)
    routing = manager_with(
        ProviderMetadata("half", prompt_cost_per_1k=1),
        ProviderMetadata("closed", prompt_cost_per_1k=1),
        health=health,
        breakers=breakers,
    )

    assert routing.route().selected_provider == "closed"


def test_doctor_reports_routing_metadata_strategy_and_integrations() -> None:
    health = healthy_registry("primary")
    routing = manager_with(ProviderMetadata("primary"), health=health)
    report = DoctorService(routing=routing).run()
    check = next(item for item in report.checks if item.name == "routing.registry")

    assert check.status is DoctorStatus.PASS
    assert check.detail["provider_count"] == 1
    assert check.detail["strategy"] == "CostAwareStrategy"
    assert check.detail["health_integration"] is True


def test_cli_routing_text_json_and_unknown_option(monkeypatch) -> None:
    health = healthy_registry("primary")
    routing = manager_with(ProviderMetadata("primary"), health=health)
    monkeypatch.setattr(ai_commands, "_service", AICommandService(routing=routing))

    text = runner.invoke(ai_commands.app, ["routing"])
    structured = runner.invoke(ai_commands.app, ["routing", "--json"])
    invalid = runner.invoke(ai_commands.app, ["routing", "--invalid"])

    assert text.exit_code == 0
    assert '"registered_providers"' in text.stdout
    assert structured.exit_code == 0
    assert '"selected_provider": "primary"' in structured.stdout
    assert invalid.exit_code == 2
