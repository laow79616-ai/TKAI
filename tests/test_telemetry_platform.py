"""Offline tests for the provider-neutral telemetry platform abstraction."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from tkai.distributed import BackendFactory
from tkai.observability import Event, EventBus
from tkai.telemetry import (
    AlwaysOffSampler,
    ConsoleExporter,
    InMemoryExporter,
    LogLevel,
    MetricKind,
    ProbabilitySampler,
    SpanStatus,
    TelemetryContext,
    TelemetryIntegration,
    TelemetryManager,
    TelemetryRuntimeAdapter,
)


def test_trace_creation_and_nested_span_parentage() -> None:
    """Spans preserve explicit trace IDs and parent-child relationships."""
    manager = TelemetryManager()
    manager.start()
    root = manager.platform.start_span("root", attributes={"kind": "request"})
    child = manager.platform.start_span("child", parent=root.context)
    finished = manager.platform.end_span(child, status=SpanStatus.OK)
    manager.platform.end_span(root)

    assert finished.parent_span_id == root.span_id
    assert finished.trace_id == root.trace_id
    assert manager.traces.snapshot()[-2].span_id == child.span_id
    assert manager.traces.snapshot()[-1].span_id == root.span_id


def test_context_propagation_and_structured_logging_links_ids() -> None:
    """A context scope is restored and its IDs reach safe structured logs."""
    manager = TelemetryManager()
    context = TelemetryContext("trace", "span", "correlation")

    assert manager.platform.current_context() is None
    with manager.platform.use_context(context):
        assert manager.platform.current_context() == context
        manager.platform.log(LogLevel.INFO, "linked", attributes={"token": "secret"})
    record = manager.logging.records[-1]

    assert manager.platform.current_context() is None
    assert record.trace_id == "trace"
    assert record.correlation_id == "correlation"
    assert record.span_id == "span"
    assert record.attributes["token"] == "***"


def test_counter_gauge_histogram_and_timer_use_existing_metric_collection() -> None:
    """Metric instruments are provider-neutral facades over immutable metric records."""
    manager = TelemetryManager()
    manager.platform.counter("requests", route="chat")
    manager.platform.gauge("workers", 2.0)
    manager.platform.histogram("latency", 3.0)
    with manager.platform.timer("elapsed"):
        pass
    metrics = manager.metrics.snapshot()

    assert [metric.kind for metric in metrics] == [
        MetricKind.COUNTER,
        MetricKind.GAUGE,
        MetricKind.HISTOGRAM,
        MetricKind.HISTOGRAM,
    ]
    assert metrics[-1].value >= 0.0


def test_sampling_is_offline_deterministic_and_configurable() -> None:
    """Always-off prevents trace collection and probability decisions are stable."""
    manager = TelemetryManager(sampler=AlwaysOffSampler())
    span = manager.platform.start_span("ignored")
    manager.platform.end_span(span)
    assert manager.traces.snapshot() == []

    sampler = ProbabilitySampler(0.5)
    assert sampler.should_sample("stable", "operation") is sampler.should_sample(
        "stable", "operation"
    )


def test_in_memory_and_console_exporters_remain_offline() -> None:
    """Exporters retain data locally and console uses an injected sink."""
    lines: list[str] = []
    manager = TelemetryManager()
    memory = InMemoryExporter()
    console = ConsoleExporter(lines.append)
    manager.register_exporter("memory", memory)
    manager.register_exporter("console", console)
    manager.start("memory")
    manager.start("console")
    manager.record(manager.platform.counter("exported"), exporter="memory")
    manager.record(manager.platform.counter("console"), exporter="console")

    assert len(memory.metrics) == 1
    assert len(lines) == 1
    assert '"metric"' in lines[0]


def test_concurrent_traces_are_isolated_and_recorded_safely() -> None:
    """ContextVars and the legacy trace registry remain safe for concurrent callers."""
    manager = TelemetryManager()

    def create(index: int) -> str:
        span = manager.platform.start_span("work", attributes={"index": index})
        return manager.platform.end_span(span).span_id

    with ThreadPoolExecutor(max_workers=8) as executor:
        span_ids = list(executor.map(create, range(24)))

    assert len(set(span_ids)) == 24
    assert len(manager.traces.snapshot()) == 48


def test_runtime_event_bus_and_factory_integrations_are_explicit() -> None:
    """Runtime and EventBus integration record signals without behavior changes."""
    manager = BackendFactory.create_telemetry_manager()
    runtime = TelemetryRuntimeAdapter(manager)
    runtime.start()
    bus = EventBus()
    integration = TelemetryIntegration(manager)
    integration.attach_event_bus(bus)
    bus.publish(Event(name="local.event"))
    integration.record_retry(attempted=True)
    integration.detach_event_bus()
    bus.publish(Event(name="ignored.event"))
    runtime.stop()

    labels = [metric.labels for metric in manager.metrics.snapshot()]
    assert {"event": "local.event"} in labels
    assert {"attempted": "true"} in labels
