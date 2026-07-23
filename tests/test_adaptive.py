"""Offline regression tests for explicit adaptive-routing foundation behavior."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from typer.testing import CliRunner

from tkai.adaptive import (
    AdaptiveRouter,
    AdaptiveRouterRegistry,
    AdaptiveRoutingManager,
    AdaptiveRoutingPolicyAdapter,
    AdaptiveRoutingRuntimeAdapter,
    AdaptiveScoringEngine,
    AdaptiveWeights,
    NoAdaptiveProviderError,
    ProviderHistory,
    ProviderSignal,
)
from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyStage

NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def _signal(provider: str, **changes: object) -> ProviderSignal:
    values: dict[str, object] = {
        "timestamp": NOW,
        "latency_ms": 100.0,
        "success": True,
        "cost": 0.1,
        "load": 0.1,
    }
    values.update(changes)
    return ProviderSignal(provider, **values)  # type: ignore[arg-type]


def test_models_weights_history_and_statistics_are_bounded_and_stable() -> None:
    with pytest.raises(ValueError):
        AdaptiveWeights(reliability=-1).validate()
    weights = AdaptiveWeights(reliability=2, latency=2, health=0, cost=0, load=0)
    assert weights.normalized().reliability == 0.5
    history = ProviderHistory(max_samples_per_provider=2)
    history.record(_signal("beta", timestamp=NOW))
    history.record(_signal("beta", timestamp=NOW + timedelta(seconds=1), success=False))
    history.record(
        _signal("beta", timestamp=NOW + timedelta(seconds=2), latency_ms=200)
    )
    statistics = history.statistics("beta")
    assert statistics.sample_count == 2
    assert statistics.success_rate == 0.5
    assert statistics.p95_latency_ms == 200
    assert history.snapshot("beta")[-1].to_dict()["timestamp"].endswith("+00:00")


def test_scoring_cold_start_ties_and_governance_filters() -> None:
    history = ProviderHistory()
    router = AdaptiveRouter(AdaptiveScoringEngine(history, minimum_samples=3))
    cold = router.select(["zeta", "alpha"])
    assert cold.selected_provider == "alpha"
    assert cold.scores[0].confidence == 0.0
    history.record(_signal("open", breaker_open=True))
    history.record(_signal("limited", rate_limited=True, load=0.9))
    scores = router.rank(["open", "limited"])
    assert not next(score for score in scores if score.provider == "open").eligible
    limited = next(score for score in scores if score.provider == "limited")
    assert limited.health_score == 0.25
    with pytest.raises(NoAdaptiveProviderError):
        router.select(["open"])


def test_router_registry_lifecycle_is_stable() -> None:
    registry = AdaptiveRouterRegistry()
    router = AdaptiveRouter(AdaptiveScoringEngine(ProviderHistory()))
    registry.register("alpha", router)
    assert [name for name, _router in registry.list()] == ["alpha"]
    registry.disable("alpha")
    assert not registry.enabled("alpha")
    registry.enable("alpha")
    assert registry.get("alpha") is router
    assert registry.unregister("alpha") is router
    registry.clear()


def test_history_thread_safety_events_and_failure_isolation() -> None:
    bus = EventBus()
    bus.subscribe(lambda _event: (_ for _ in ()).throw(RuntimeError("observer")))
    manager = AdaptiveRoutingManager(event_bus=bus)
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda number: manager.record_signal(_signal("local", cost=number)),
                range(40),
            )
        )
    assert manager.statistics("local").sample_count == 40
    assert manager.events
    manager.clear()
    assert manager.statistics("local").sample_count == 0


def test_manager_runtime_policy_doctor_and_cli_are_explicit(monkeypatch) -> None:
    manager = AdaptiveRoutingManager()
    runtime = AdaptiveRoutingRuntimeAdapter(manager)
    runtime.record_attempt("first", _signal("primary"))
    runtime.record_attempt("first", _signal("primary", success=False))
    runtime.record_attempt("cached", _signal("primary"), cache_hit=True)
    assert manager.statistics("primary").sample_count == 1
    policy = AdaptiveRoutingPolicyAdapter(manager, allow_provider_override=True)
    context = PolicyContext(
        PolicyStage.BEFORE_ROUTING,
        {"adaptive_candidates": ["primary", "backup"]},
    )
    policy.apply(context)
    assert context.data["adaptive_decision"].selected_provider == "primary"
    report = DoctorService(adaptive=manager).run()
    check = next(item for item in report.checks if item.name == "adaptive_routing")
    assert check.status is DoctorStatus.PASS
    monkeypatch.setattr(ai_commands, "_service", AICommandService(adaptive=manager))
    result = CliRunner().invoke(ai_commands.app, ["adaptive-routing", "--json"])
    assert result.exit_code == 0
    assert '"enabled": true' in result.stdout


def test_fallback_and_shutdown_are_safe() -> None:
    history = ProviderHistory()
    history.record(_signal("blocked", breaker_open=True))
    router = AdaptiveRouter(
        AdaptiveScoringEngine(history),
        fallback=lambda candidates: candidates[-1],
    )
    decision = router.select(["blocked"])
    assert decision.fallback_used
    manager = AdaptiveRoutingManager()
    manager.shutdown()
    manager.record_signal(_signal("ignored"))
    assert manager.statistics("ignored").sample_count == 0
