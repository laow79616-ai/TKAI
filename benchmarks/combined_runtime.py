"""Pure local composition benchmark; it never invokes a provider or network."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from benchmarks import (
    BenchmarkReport,
    BenchmarkResult,
    BenchmarkRunner,
    HighResolutionTimer,
)
from benchmarks.policy import _StaticPolicy
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.multiregion import MultiRegionManager, Region
from tkai.observability import Event, EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.retry import RetryPolicy
from tkai.telemetry import Metric, TelemetryManager


@dataclass(slots=True)
class CombinedRuntimeBenchmark:
    """Use existing managers around one deterministic local Runtime stub."""

    policy: PolicyManager = field(init=False)
    regions: MultiRegionManager = field(init=False)
    adaptive: AdaptiveRoutingManager = field(init=False)
    retry: RetryPolicy = field(init=False)
    telemetry: TelemetryManager = field(init=False)
    bus: EventBus = field(init=False)
    stage_counts: dict[str, int] = field(default_factory=dict, init=False)
    stage_elapsed_ns: dict[str, int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.bus = EventBus()
        self.policy = PolicyManager(event_bus=self.bus)
        self.policy.register(_StaticPolicy("combined", True))
        self.regions = MultiRegionManager(event_bus=self.bus)
        self.regions.register_region(Region("local", priority=1, latency_estimate_ms=1))
        self.adaptive = AdaptiveRoutingManager(event_bus=self.bus)
        self.adaptive.record_signal(
            ProviderSignal("local", datetime.now(timezone.utc), latency_ms=1.0)
        )
        self.retry = RetryPolicy("combined", max_attempts=2)
        self.telemetry = TelemetryManager(event_bus=self.bus)
        self.telemetry.start()

    def _stage(self, name: str, operation: object) -> None:
        timer = HighResolutionTimer().start()
        operation()
        elapsed = timer.stop()
        self.stage_counts[name] = self.stage_counts.get(name, 0) + 1
        self.stage_elapsed_ns[name] = self.stage_elapsed_ns.get(name, 0) + elapsed

    def operation(self) -> None:
        context = PolicyContext(PolicyStage.BEFORE_REQUEST)
        self._stage("policy", lambda: self.policy.execute(context))
        self._stage("region", self.regions.select_region)
        self._stage("adaptive", lambda: self.adaptive.rank_providers(("local",)))
        self._stage(
            "retry",
            lambda: self.retry.decide(TimeoutError("offline"), 1, self.retry.budget()),
        )
        self._stage("runtime", lambda: "fixed-response")
        self._stage("telemetry", lambda: self.telemetry.record(Metric("combined", 1)))
        self._stage("eventbus", lambda: self.bus.publish(Event("combined")))
        self.bus.events.clear()
        self.policy.engine.events.clear()
        self.regions.events.clear()
        self.adaptive.events.clear()
        self.telemetry.events.clear()
        self.telemetry.metrics.clear()
        self.telemetry.registry.get("local").metrics.clear()

    def run(self, iterations: int = 5) -> BenchmarkResult:
        return BenchmarkRunner(iterations=iterations, random_seed=17).run(
            self.operation
        )


def run_benchmark(iterations: int = 5) -> BenchmarkResult:
    return CombinedRuntimeBenchmark().run(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("combined_runtime", run_benchmark())
