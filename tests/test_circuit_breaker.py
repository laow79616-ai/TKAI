"""Offline regression tests for the passive circuit breaker foundation."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerError,
    CircuitBreakerManager,
    CircuitBreakerNotFoundError,
    CircuitBreakerRegistry,
    CircuitState,
    ThresholdStrategy,
)
from tkai.commands import ai as ai_commands
from tkai.health import HealthEvent, HealthStatus

runner = CliRunner()


class MutableClock:
    """Deterministic timezone-aware clock for state-machine tests."""

    def __init__(self) -> None:
        self.now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: int) -> None:
        self.now += timedelta(seconds=seconds)


def strategy() -> ThresholdStrategy:
    """Create compact deterministic thresholds for test state transitions."""
    return ThresholdStrategy(
        failure_threshold=2,
        open_duration=timedelta(seconds=10),
        half_open_success_threshold=2,
    )


def test_state_machine_transition_and_json_snapshot() -> None:
    clock = MutableClock()
    breaker = CircuitBreaker("primary", strategy=strategy(), clock=clock)

    breaker.record_failure()
    assert breaker.snapshot.state is CircuitState.CLOSED
    breaker.record_failure()
    assert breaker.snapshot.state is CircuitState.OPEN
    assert not breaker.allow_request()
    clock.advance(10)
    assert breaker.allow_request()
    assert breaker.snapshot.state is CircuitState.HALF_OPEN
    breaker.record_success()
    assert breaker.snapshot.state is CircuitState.HALF_OPEN
    breaker.record_success()

    snapshot = breaker.snapshot
    assert snapshot.state is CircuitState.CLOSED
    assert json.loads(json.dumps(snapshot.to_dict()))["state"] == "closed"
    assert [event.event for event in breaker.events] == [
        "BreakerOpened",
        "BreakerHalfOpen",
        "BreakerClosed",
    ]


def test_half_open_failure_reopens_and_reset_is_unified() -> None:
    clock = MutableClock()
    breaker = CircuitBreaker("primary", strategy=strategy(), clock=clock)
    breaker.record_failure()
    breaker.record_failure()
    clock.advance(10)
    assert breaker.allow_request()
    breaker.record_failure(reason="probe failed")

    assert breaker.snapshot.state is CircuitState.OPEN
    breaker.reset()
    assert breaker.snapshot.state is CircuitState.CLOSED
    assert breaker.snapshot.failure_count == 0
    assert breaker.events[-1].event == "BreakerReset"


def test_registry_has_stable_order_duplicate_protection_and_clear() -> None:
    registry = CircuitBreakerRegistry()
    registry.register("secondary")
    registry.register("primary")

    assert [breaker.provider for breaker in registry.list()] == ["primary", "secondary"]
    with pytest.raises(CircuitBreakerError):
        registry.register("primary")
    with pytest.raises(CircuitBreakerNotFoundError):
        registry.get("missing")
    registry.reset("primary")
    registry.clear()
    assert registry.list() == []


def test_health_events_passively_update_breaker_without_network_access() -> None:
    manager = CircuitBreakerManager(strategy=strategy())
    now = datetime.now(timezone.utc)
    unhealthy = HealthEvent(
        "primary",
        "ProviderUnhealthy",
        HealthStatus.DEGRADED,
        HealthStatus.UNHEALTHY,
        now,
    )
    recovered = HealthEvent(
        "primary",
        "ProviderRecovered",
        HealthStatus.UNHEALTHY,
        HealthStatus.HEALTHY,
        now,
    )
    reset = HealthEvent(
        "primary",
        "ProviderReset",
        HealthStatus.HEALTHY,
        HealthStatus.UNKNOWN,
        now,
    )

    assert manager.handle_health_event(unhealthy).state is CircuitState.OPEN
    manager.handle_health_event(recovered)
    assert manager.list()[0].success_count == 1
    assert manager.handle_health_event(reset).state is CircuitState.CLOSED


def test_doctor_reports_breaker_registry_states_and_strategy() -> None:
    manager = CircuitBreakerManager()
    manager.register("primary")
    report = DoctorService(circuit_breaker=manager).run()
    check = next(
        item for item in report.checks if item.name == "circuit_breaker.registry"
    )

    assert check.status is DoctorStatus.PASS
    assert check.detail["provider_count"] == 1
    assert check.detail["states"] == {"primary": "closed"}
    assert check.detail["strategy"] == "ThresholdStrategy"


def test_cli_breaker_text_json_and_unknown_option(monkeypatch) -> None:
    manager = CircuitBreakerManager()
    manager.register("primary")
    monkeypatch.setattr(
        ai_commands, "_service", AICommandService(circuit_breaker=manager)
    )

    text = runner.invoke(ai_commands.app, ["breaker"])
    structured = runner.invoke(ai_commands.app, ["breaker", "--json"])
    invalid = runner.invoke(ai_commands.app, ["breaker", "--invalid"])

    assert text.exit_code == 0
    assert '"provider": "primary"' in text.stdout
    assert structured.exit_code == 0
    assert json.loads(structured.stdout)[0]["state"] == "closed"
    assert invalid.exit_code == 2
