"""Offline regression tests for local quota management and routing composition."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.health import HealthRegistry, HealthSnapshot, HealthStatus
from tkai.observability import EventBus, EventDispatcher, MetricsAdapter
from tkai.rate_limit import (
    FixedWindowStrategy,
    QuotaNotFoundError,
    QuotaRegistry,
    RateLimitAwareStrategy,
    RateLimitManager,
    RateLimitSnapshot,
    SlidingWindowStrategy,
)
from tkai.routing import CostAwareStrategy, ProviderMetadata, RoutingManager

runner = CliRunner()


class MutableClock:
    """Simple deterministic UTC clock for window strategy tests."""

    def __init__(self) -> None:
        self.value = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, seconds: int) -> None:
        self.value += timedelta(seconds=seconds)


def quota(provider: str, **values: object) -> RateLimitSnapshot:
    """Create one compact configured provider quota snapshot."""
    defaults: dict[str, object] = {
        "requests_per_second": 2,
        "requests_per_minute": 3,
        "tokens_per_minute": 10,
    }
    defaults.update(values)
    return RateLimitSnapshot(provider, **defaults)  # type: ignore[arg-type]


def test_snapshot_validation_serialization_and_quota_registry() -> None:
    value = quota("primary")
    registry = QuotaRegistry()
    registry.register(value)

    assert registry.get("primary") == value
    assert registry.list() == [value]
    assert value.to_dict()["provider"] == "primary"
    with pytest.raises(ValueError):
        RateLimitSnapshot("bad", requests_per_minute=-1)
    with pytest.raises(QuotaNotFoundError):
        registry.get("missing")
    assert registry.reset("primary").current_requests == 0
    registry.clear()
    assert registry.list() == []


def test_sliding_window_remaining_quota_and_reset() -> None:
    clock = MutableClock()
    manager = RateLimitManager(strategy=SlidingWindowStrategy(clock))
    manager.register(quota("primary"))

    assert manager.consume("primary", tokens=4)
    assert manager.consume("primary", tokens=4)
    assert not manager.consume("primary", tokens=4)
    current = manager.list()[0]
    assert current.current_requests == 2
    assert current.current_tokens == 8
    assert current.remaining_requests == 1
    assert current.remaining_tokens == 2
    assert current.reset_at is not None

    clock.advance(60)
    assert manager.allow("primary", tokens=10)
    reset = manager.reset("primary")
    assert reset.current_requests == 0
    assert reset.remaining_tokens == 10


def test_fixed_window_applies_request_per_second_and_minute_limits() -> None:
    clock = MutableClock()
    manager = RateLimitManager(strategy=FixedWindowStrategy(clock))
    manager.register(quota("primary", requests_per_second=1, requests_per_minute=2))

    assert manager.consume("primary")
    assert not manager.consume("primary")
    clock.advance(1)
    assert manager.consume("primary")
    assert not manager.consume("primary")


def test_quota_events_publish_to_existing_event_bus_and_metrics() -> None:
    bus = EventBus()
    metrics = MetricsAdapter()
    bus.subscribe(EventDispatcher([metrics]).dispatch)
    manager = RateLimitManager(event_bus=bus)
    manager.register(quota("primary", requests_per_second=1, requests_per_minute=1))

    assert manager.consume("primary")
    assert not manager.consume("primary")
    manager.reset("primary")

    assert [event.name for event in manager.events] == [
        "QuotaConsumed",
        "RateLimitExceeded",
        "QuotaReset",
    ]
    assert metrics.counts["RateLimitExceeded"] == 1
    assert metrics.counts["QuotaConsumed"] == 1


def test_rate_limit_aware_strategy_excludes_exhausted_provider() -> None:
    clock = MutableClock()
    limiter = RateLimitManager(strategy=SlidingWindowStrategy(clock))
    limiter.register(quota("cheap", requests_per_minute=1))
    limiter.register(quota("backup", requests_per_minute=2))
    assert limiter.consume("cheap")
    health = HealthRegistry()
    for provider in ("cheap", "backup"):
        health.update(HealthSnapshot(provider, status=HealthStatus.HEALTHY))
    routing = RoutingManager(
        strategy=RateLimitAwareStrategy(
            limiter.registry, CostAwareStrategy(), limiter.strategy
        ),
        health_registry=health,
    )
    routing.register(ProviderMetadata("cheap", prompt_cost_per_1k=0.1))
    routing.register(ProviderMetadata("backup", prompt_cost_per_1k=1.0))

    assert routing.route().selected_provider == "backup"


def test_doctor_and_cli_rate_limit_outputs(monkeypatch) -> None:
    bus = EventBus()
    manager = RateLimitManager(event_bus=bus)
    manager.register(quota("primary"))
    report = DoctorService(rate_limit=manager).run()
    check = next(item for item in report.checks if item.name == "rate_limit.registry")
    assert check.status is DoctorStatus.PASS
    assert check.detail["event_bus_available"] is True

    monkeypatch.setattr(ai_commands, "_service", AICommandService(rate_limit=manager))
    text = runner.invoke(ai_commands.app, ["rate-limit"])
    structured = runner.invoke(ai_commands.app, ["rate-limit", "--json"])
    invalid = runner.invoke(ai_commands.app, ["rate-limit", "--invalid"])
    assert text.exit_code == 0
    assert '"provider": "primary"' in text.stdout
    assert structured.exit_code == 0
    assert '"remaining_requests": 3' in structured.stdout
    assert invalid.exit_code == 2
