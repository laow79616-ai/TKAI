"""Deterministic local failure injection with recovery and isolation checks."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from benchmarks.combined_runtime import CombinedRuntimeBenchmark
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.distributed import DistributedCoordinator, LocalBackend, Node
from tkai.multiregion import MultiRegionManager, NoRegionAvailableError, Region
from tkai.observability import Event, EventBus
from tkai.policy import PolicyContext, PolicyDecision, PolicyManager, PolicyStage
from tkai.retry import RetryManager, RetryPolicy
from tkai.telemetry import LocalExporter, Metric, TelemetryManager


class _FailingPolicy:
    def name(self) -> str:
        return "failing"

    def priority(self) -> int:
        return 1

    def enabled(self) -> bool:
        return True

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        del context
        raise RuntimeError("injected")

    def apply(self, context: PolicyContext) -> None:
        del context

    def shutdown(self) -> None:
        return None


class _FailingExporter(LocalExporter):
    def export_metric(self, metric: Metric) -> None:
        del metric
        raise RuntimeError("injected exporter failure")


def _node() -> Node:
    now = datetime.now(timezone.utc)
    return Node("local", "localhost", now, now)


def test_policy_retry_telemetry_and_subscriber_failures_are_isolated() -> None:
    """Failure of optional observers or policies does not corrupt later local work."""
    policy = PolicyManager()
    policy.register(_FailingPolicy())
    outcome = policy.execute(PolicyContext(PolicyStage.BEFORE_REQUEST))
    assert outcome[0].outcome == "failed"

    manager = RetryManager()
    broken = RetryPolicy(
        "broken",
        classifier=lambda error: (_ for _ in ()).throw(RuntimeError("classifier")),
    )
    with pytest.raises(RuntimeError, match="classifier"):
        manager.run(
            lambda: (_ for _ in ()).throw(TimeoutError("offline")), policy=broken
        )
    assert (
        manager.run(lambda: "recovered", policy=RetryPolicy("healthy")) == "recovered"
    )

    telemetry = TelemetryManager()
    telemetry.register_exporter("broken", _FailingExporter())
    telemetry.record(Metric("failure", 1), exporter="broken")
    telemetry.record(Metric("recovered", 1))
    assert [metric.name for metric in telemetry.metrics.snapshot()] == [
        "failure",
        "recovered",
    ]

    bus = EventBus()
    delivered: list[str] = []
    bus.subscribe(lambda event: (_ for _ in ()).throw(RuntimeError("subscriber")))
    bus.subscribe(lambda event: delivered.append(event.name))
    bus.publish(Event("recovered"))
    assert delivered == ["recovered"]


def test_backend_routing_region_and_combined_runtime_recover_after_fail_once(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Restore deterministic local paths after each injected single failure."""
    backend = LocalBackend()
    original_set = backend.set
    failed = False

    def fail_once(key: str, value: object) -> None:
        nonlocal failed
        if not failed:
            failed = True
            raise RuntimeError("backend")
        original_set(key, value)

    monkeypatch.setattr(backend, "set", fail_once)
    with pytest.raises(RuntimeError, match="backend"):
        backend.set("local", 1)
    backend.set("local", 2)
    assert backend.get("local") == 2

    adaptive = AdaptiveRoutingManager()
    original_record = adaptive.history.record
    monkeypatch.setattr(
        adaptive.history,
        "record",
        lambda signal: (_ for _ in ()).throw(RuntimeError("history")),
    )
    with pytest.raises(RuntimeError, match="history"):
        adaptive.record_signal(ProviderSignal("local", datetime.now(timezone.utc)))
    monkeypatch.setattr(adaptive.history, "record", original_record)
    adaptive.record_signal(ProviderSignal("local", datetime.now(timezone.utc)))
    assert adaptive.rank_providers(("local",))[0].provider == "local"

    regions = MultiRegionManager()
    with pytest.raises(NoRegionAvailableError):
        regions.select_region()
    regions.register_region(Region("local"))
    assert regions.select_region().selected_region == "local"

    benchmark = CombinedRuntimeBenchmark()
    original_decide = benchmark.retry.decide
    monkeypatch.setattr(
        benchmark.retry,
        "decide",
        lambda error, attempt, budget: (_ for _ in ()).throw(RuntimeError("stage")),
    )
    with pytest.raises(RuntimeError, match="stage"):
        benchmark.operation()
    monkeypatch.setattr(benchmark.retry, "decide", original_decide)
    assert benchmark.run(iterations=1).operations == 1
    assert benchmark.bus.events == []

    coordinator = DistributedCoordinator(_node(), backend=backend)
    original_connect = backend.connect
    monkeypatch.setattr(
        backend, "connect", lambda: (_ for _ in ()).throw(RuntimeError("connect"))
    )
    with pytest.raises(RuntimeError, match="connect"):
        coordinator.start()
    monkeypatch.setattr(backend, "connect", original_connect)
    coordinator.start()
    coordinator.stop()
