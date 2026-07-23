"""Offline tests for explicit adaptive runtime scheduling."""

from concurrent.futures import ThreadPoolExecutor

from tkai.runtime_scheduler import RuntimeScheduler, SchedulingPolicy


def scheduler() -> RuntimeScheduler:
    value = RuntimeScheduler(failure_threshold=2, recovery_timeout_seconds=0)
    value.register("fast", latency_ms=5, cost=2, priority=1, weight=2)
    value.register("cheap", latency_ms=20, cost=1, priority=0, weight=1)
    return value


def test_scoring_and_basic_policy_selection() -> None:
    value = scheduler()
    assert value.schedule(SchedulingPolicy.LEAST_LATENCY).provider == "fast"
    assert value.schedule(SchedulingPolicy.LOWEST_COST).provider == "cheap"
    assert value.schedule(SchedulingPolicy.HIGHEST_SCORE).scores


def test_round_robin_weighted_and_sticky_scheduling() -> None:
    value = scheduler()
    assert [
        value.schedule(SchedulingPolicy.ROUND_ROBIN).provider for _ in range(2)
    ] == ["cheap", "fast"]
    assert value.schedule(SchedulingPolicy.WEIGHTED_ROUND_ROBIN).provider == "fast"
    first = value.schedule(SchedulingPolicy.STICKY_SESSION, session_id="one").provider
    assert (
        value.schedule(SchedulingPolicy.STICKY_SESSION, session_id="one").provider
        == first
    )


def test_error_cost_and_adaptive_results_use_recorded_data() -> None:
    value = scheduler()
    value.record_result("fast", success=False, latency_ms=50)
    value.record_result("fast", success=False)
    assert value.schedule(SchedulingPolicy.LEAST_ERROR).provider == "cheap"
    assert value.schedule(SchedulingPolicy.ADAPTIVE).provider == "cheap"


def test_reused_circuit_breaker_excludes_open_provider() -> None:
    value = scheduler()
    value.record_result("fast", success=False)
    value.record_result("fast", success=False)
    assert value.schedule().provider == "cheap"


def test_concurrent_scheduling_is_thread_safe_and_offline() -> None:
    value = scheduler()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: value.schedule(), range(32)))
    assert all(item.provider in {"fast", "cheap"} for item in results)
