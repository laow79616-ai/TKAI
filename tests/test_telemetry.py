"""Offline telemetry foundation regression tests."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from typer.testing import CliRunner

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.commands import ai as ai_commands
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.telemetry import (
    CorrelationContext,
    LocalExporter,
    Metric,
    TelemetryManager,
    TelemetryPolicyAdapter,
    TelemetryRuntimeAdapter,
)


class _FailingExporter(LocalExporter):
    def export_metric(self, metric: Metric) -> None:
        raise RuntimeError("export unavailable")


def test_export_metrics_traces_context_and_safe_logs() -> None:
    manager = TelemetryManager()
    manager.start()
    manager.record(Metric("requests", 1))
    trace = manager.begin_span("chat")
    manager.end_span(trace)
    record = manager.log(
        "info",
        "safe",
        attributes={"api_key": "secret", "nested": {"token": "also-secret"}},
    )
    assert manager.summary()["metrics"] == 1
    assert manager.summary()["traces"] == 2
    assert record.attributes["api_key"] == "***"
    assert record.attributes["nested"] == {"token": "***"}
    context = CorrelationContext(request_id="one").inherit(trace_id="two")
    assert context.to_dict()["trace_id"] == "two"
    assert context.copy() == context


def test_runtime_policy_doctor_and_cli_are_explicit(monkeypatch) -> None:
    manager = TelemetryManager()
    runtime = TelemetryRuntimeAdapter(manager)
    assert not manager.summary()["exporters"][0]["healthy"]
    runtime.start()
    policies = PolicyManager()
    policies.register(TelemetryPolicyAdapter(manager))
    context = PolicyContext(PolicyStage.BEFORE_REQUEST)
    policies.execute(context)
    assert context.data["telemetry_manager"] is manager
    report = DoctorService(telemetry=manager).run()
    telemetry_check = next(
        check for check in report.checks if check.name == "telemetry.registry"
    )
    assert telemetry_check.status is DoctorStatus.PASS
    monkeypatch.setattr(ai_commands, "_service", AICommandService(telemetry=manager))
    result = CliRunner().invoke(ai_commands.app, ["telemetry", "--json"])
    assert result.exit_code == 0
    assert '"metrics": 0' in result.stdout


def test_async_exporter_and_event_bus_are_local_only() -> None:
    async def exercise() -> None:
        exporter = LocalExporter()
        await exporter.async_start()
        await exporter.async_export_metric(Metric("async.requests", 1))
        assert exporter.health()
        assert len(exporter.metrics) == 1
        await exporter.async_stop()
        assert not exporter.health()

    bus = EventBus()
    manager = TelemetryManager(event_bus=bus)
    manager.start()
    manager.record(Metric("events", 1))
    assert [event.name for event in bus.events][-2:] == [
        "TelemetryStarted",
        "MetricRecorded",
    ]
    asyncio.run(exercise())


def test_collector_thread_safety_and_export_failure_isolation() -> None:
    manager = TelemetryManager()
    manager.register_exporter("failing", _FailingExporter())
    manager.record(Metric("failure.isolated", 1), exporter="failing")
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: manager.record(Metric("concurrent", index)),
                range(40),
            )
        )
    assert len(manager.metrics.snapshot()) == 41
    assert len(manager.traces.snapshot()) == 0
