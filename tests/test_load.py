"""Offline coverage for passive local load collection and load-aware routing."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerRegistry,
    ThresholdStrategy,
)
from tkai.commands import ai as ai_commands
from tkai.health import HealthRegistry, HealthSnapshot, HealthStatus
from tkai.load import (
    LatencyStatistics,
    LoadAwareStrategy,
    LoadEvaluator,
    LoadManager,
    LoadRegistry,
    LoadStatus,
    LoadThresholds,
    PassiveLoadCollector,
    ProviderLoadNotFoundError,
    ProviderLoadSnapshot,
)
from tkai.observability import (
    EventBus,
    EventDispatcher,
    MetricsAdapter,
    ProviderFailed,
    RequestCompleted,
    RequestStarted,
)
from tkai.routing import CostAwareStrategy, ProviderMetadata, RoutingManager

runner = CliRunner()


def snapshot(provider: str, **values: object) -> ProviderLoadSnapshot:
    """Build an evaluated local snapshot with a deterministic UTC update time."""
    return ProviderLoadSnapshot(
        provider,
        last_updated=datetime.now(timezone.utc),
        **values,
    )


def test_snapshot_validation_utc_serialization_and_immutable_fields() -> None:
    value = snapshot("primary", active_requests=1, utilization=0.1)

    assert value.to_dict()["last_updated"].endswith("+00:00")
    with pytest.raises(ValueError):
        ProviderLoadSnapshot("bad", active_requests=-1)
    with pytest.raises(ValueError):
        ProviderLoadSnapshot("bad", error_rate=1.1)
    with pytest.raises(ValueError):
        ProviderLoadSnapshot("bad", average_latency_ms=-1)


def test_registry_operations_stable_order_and_thread_safe_registration() -> None:
    registry = LoadRegistry()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(executor.map(registry.register, ("delta", "alpha", "charlie", "bravo")))

    assert [item.provider for item in registry.list()] == [
        "alpha",
        "bravo",
        "charlie",
        "delta",
    ]
    registry.update(snapshot("alpha", completed_requests=2, status=LoadStatus.LOW))
    assert registry.get("alpha").completed_requests == 2
    assert registry.reset("alpha").status is LoadStatus.UNKNOWN
    assert registry.remove("bravo").provider == "bravo"
    with pytest.raises(ProviderLoadNotFoundError):
        registry.get("bravo")
    registry.clear()
    assert registry.list() == []


def test_passive_collector_event_bus_counts_latency_and_never_negative() -> None:
    bus = EventBus()
    metrics = MetricsAdapter()
    bus.subscribe(EventDispatcher([metrics]).dispatch)
    manager = LoadManager(event_bus=bus, capacity=10, max_latency_samples=3)

    bus.publish(RequestStarted(data={"provider": "primary"}))
    bus.publish(RequestCompleted(data={"provider": "primary", "latency_ms": 20}))
    bus.publish(
        ProviderFailed(data={"provider": "primary", "timeout": True, "latency_ms": 40})
    )
    bus.publish(RequestCompleted(data={"provider": "primary", "latency_ms": 10}))

    value = manager.get("primary")
    assert value.active_requests == 0
    assert value.completed_requests == 2
    assert value.failed_requests == 1
    assert value.timeout_requests == 1
    assert value.average_latency_ms == pytest.approx(70 / 3)
    assert value.p95_latency_ms == 40
    assert value.p99_latency_ms == 40
    assert value.error_rate == pytest.approx(1 / 3)
    assert manager.collector.event_bus is bus
    assert metrics.counts["LoadChanged"] == 1


def test_bounded_latency_statistics_and_deterministic_percentiles() -> None:
    statistics = LatencyStatistics(max_samples=3)
    for item in (5, 100, 10, 20):
        statistics.add(item)

    assert statistics.size == 3
    assert statistics.snapshot() == pytest.approx((130 / 3, 100, 100))
    assert LatencyStatistics().snapshot() == (0.0, 0.0, 0.0)


def test_evaluator_thresholds_and_load_events_only_on_status_change() -> None:
    evaluator = LoadEvaluator(
        LoadThresholds(
            low_utilization=0.3,
            normal_utilization=0.7,
            high_utilization=0.9,
            high_pending_requests=2,
            high_latency_ms=10,
            high_error_rate=0.2,
        )
    )
    assert evaluator.evaluate(ProviderLoadSnapshot("unknown")) is LoadStatus.UNKNOWN
    assert evaluator.evaluate(snapshot("low", utilization=0.2)) is LoadStatus.LOW
    assert evaluator.evaluate(snapshot("normal", utilization=0.5)) is LoadStatus.NORMAL
    assert evaluator.evaluate(snapshot("high", utilization=0.8)) is LoadStatus.HIGH
    assert (
        evaluator.evaluate(snapshot("saturated", utilization=0.9))
        is LoadStatus.SATURATED
    )

    bus = EventBus()
    collector = PassiveLoadCollector(LoadRegistry(), event_bus=bus)
    collector.request_started("primary")
    collector.request_started("primary")
    assert [event.name for event in collector.events] == ["LoadChanged"]


def test_load_strategy_handles_unknown_health_and_breaker_signals() -> None:
    health = HealthRegistry()
    for provider in ("unknown", "low", "busy", "unhealthy", "open"):
        health.update(HealthSnapshot(provider, status=HealthStatus.HEALTHY))
    health.update(HealthSnapshot("unhealthy", status=HealthStatus.UNHEALTHY))
    loads = LoadRegistry()
    for value in (
        snapshot("low", active_requests=1, utilization=0.1, status=LoadStatus.LOW),
        snapshot("busy", active_requests=8, utilization=0.8, status=LoadStatus.HIGH),
        snapshot(
            "unhealthy", active_requests=0, utilization=0.1, status=LoadStatus.LOW
        ),
        snapshot("open", active_requests=0, utilization=0.1, status=LoadStatus.LOW),
    ):
        loads.register(value.provider)
        loads.update(value)
    breakers = CircuitBreakerRegistry()
    opened = CircuitBreaker("open", strategy=ThresholdStrategy(failure_threshold=1))
    opened.record_failure()
    breakers.register("open", opened)
    routing = RoutingManager(
        strategy=LoadAwareStrategy(loads),
        health_registry=health,
        breaker_registry=breakers,
    )
    for provider, cost in (
        ("unknown", 0.0),
        ("low", 1.0),
        ("busy", 1.0),
        ("unhealthy", 0.0),
        ("open", 0.0),
    ):
        routing.register(ProviderMetadata(provider, prompt_cost_per_1k=cost))

    decision = routing.route()

    assert decision.selected_provider == "low"
    assert decision.candidate_providers == ("low", "busy")


def test_cost_then_load_tie_breaker_and_cost_strategy_regression() -> None:
    health = HealthRegistry()
    loads = LoadRegistry()
    for provider, active in (("beta", 1), ("alpha", 1)):
        health.update(HealthSnapshot(provider, status=HealthStatus.HEALTHY))
        loads.register(provider)
        loads.update(
            snapshot(
                provider,
                active_requests=active,
                utilization=0.1,
                status=LoadStatus.LOW,
            )
        )
    load_routing = RoutingManager(
        strategy=LoadAwareStrategy(loads), health_registry=health
    )
    cost_routing = RoutingManager(strategy=CostAwareStrategy(), health_registry=health)
    for manager in (load_routing, cost_routing):
        manager.register(ProviderMetadata("beta", prompt_cost_per_1k=1))
        manager.register(ProviderMetadata("alpha", prompt_cost_per_1k=1))

    assert load_routing.route().selected_provider == "alpha"
    assert cost_routing.route().selected_provider == "alpha"


def test_doctor_pass_warning_error_and_cli_text_json(monkeypatch) -> None:
    bus = EventBus()
    manager = LoadManager(event_bus=bus)
    manager.collector.request_started("primary")
    routing = RoutingManager(strategy=LoadAwareStrategy(manager.registry))
    report = DoctorService(load=manager, routing=routing).run()
    check = next(item for item in report.checks if item.name == "load.registry")
    assert check.status is DoctorStatus.PASS
    assert check.detail["event_bus_subscribed"] is True
    assert check.detail["routing_strategy_integration"] is True

    empty = DoctorService(load=LoadManager()).run()
    empty_check = next(item for item in empty.checks if item.name == "load.registry")
    assert empty_check.status is DoctorStatus.WARNING

    manager.registry.update(
        snapshot("primary", utilization=1.0, status=LoadStatus.SATURATED)
    )
    saturated = DoctorService(load=manager).run()
    saturated_check = next(
        item for item in saturated.checks if item.name == "load.registry"
    )
    assert saturated_check.status is DoctorStatus.ERROR

    monkeypatch.setattr(ai_commands, "_service", AICommandService(load=manager))
    text = runner.invoke(ai_commands.app, ["load"])
    structured = runner.invoke(ai_commands.app, ["load", "--json"])
    invalid = runner.invoke(ai_commands.app, ["load", "--invalid"])
    assert text.exit_code == 0
    assert '"provider": "primary"' in text.stdout
    assert structured.exit_code == 0
    assert '"status": "saturated"' in structured.stdout
    assert invalid.exit_code == 2
