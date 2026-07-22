"""Offline regression coverage for observability foundation integration."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.ai import DoctorService, DoctorStatus
from tkai.ai.cli_service import AICommandService
from tkai.observability import (
    EventBus,
    EventDispatcher,
    LoggerAdapter,
    MetricsAdapter,
    ProviderSelected,
    RequestCompleted,
    RequestStarted,
    TraceAdapter,
)


def observability_stack() -> tuple[
    EventBus,
    EventDispatcher,
    MetricsAdapter,
    LoggerAdapter,
    TraceAdapter,
]:
    """Create one fully in-memory, event-dispatching observability stack."""
    metrics = MetricsAdapter()
    logger = LoggerAdapter()
    trace = TraceAdapter()
    dispatcher = EventDispatcher([metrics, logger, trace])
    bus = EventBus()
    bus.subscribe(dispatcher.dispatch)
    return bus, dispatcher, metrics, logger, trace


def test_typed_events_are_immutable_and_keep_trace_correlation_metadata() -> None:
    event = RequestStarted(
        trace_id="trace-1", correlation_id="request-1", data={"provider": "test"}
    )

    assert event.name == "RequestStarted"
    assert event.trace_id == "trace-1"
    assert event.correlation_id == "request-1"
    assert event.timestamp.tzinfo is not None
    with pytest.raises(FrozenInstanceError):
        event.trace_id = "new-trace"  # type: ignore[misc]


def test_event_bus_dispatcher_and_adapters_collect_events_offline() -> None:
    bus, _, metrics, logger, trace = observability_stack()

    bus.publish(RequestStarted(trace_id="trace-1", correlation_id="request-1"))
    bus.publish(RequestCompleted(trace_id="trace-1", correlation_id="request-1"))
    bus.publish(ProviderSelected())

    assert [event.name for event in bus.events] == [
        "RequestStarted",
        "RequestCompleted",
        "ProviderSelected",
    ]
    assert metrics.counts == {
        "RequestStarted": 1,
        "RequestCompleted": 1,
        "ProviderSelected": 1,
    }
    assert '"correlation_id": "request-1"' in logger.records[0]
    assert [span.span_id for span in trace.spans] == [
        "RequestStarted",
        "RequestCompleted",
    ]


def test_event_bus_unsubscribe_and_clear_are_deterministic() -> None:
    bus = EventBus()
    received: list[str] = []

    def handler(event: RequestStarted) -> None:
        received.append(event.name)

    bus.subscribe(handler)
    bus.subscribe(handler)
    bus.publish(RequestStarted())
    bus.unsubscribe(handler)
    bus.publish(RequestCompleted())
    bus.clear()

    assert received == ["RequestStarted"]
    assert bus.events == []


def test_doctor_reports_observability_wiring_and_safe_recent_events() -> None:
    bus, dispatcher, metrics, logger, trace = observability_stack()
    bus.publish(RequestStarted(trace_id="trace-1", correlation_id="request-1"))
    report = DoctorService(
        observability_bus=bus,
        observability_dispatcher=dispatcher,
        metrics_adapter=metrics,
        logger_adapter=logger,
        trace_adapter=trace,
    ).run()
    checks = {item.name: item for item in report.checks}

    assert checks["observability.event_bus"].status is DoctorStatus.PASS
    assert checks["observability.dispatcher"].status is DoctorStatus.PASS
    assert checks["observability.subscribers"].detail["count"] == 3
    assert checks["observability.metrics"].status is DoctorStatus.PASS
    assert checks["observability.logger"].status is DoctorStatus.PASS
    assert checks["observability.trace"].status is DoctorStatus.PASS
    assert checks["observability.event_bus"].detail["recent_events"] == [
        "RequestStarted"
    ]


def test_cli_service_exposes_safe_observability_summary() -> None:
    bus, dispatcher, metrics, logger, trace = observability_stack()
    bus.publish(RequestStarted(trace_id="trace-1", correlation_id="request-1"))
    service = AICommandService(
        observability_bus=bus,
        observability_dispatcher=dispatcher,
        metrics_adapter=metrics,
        logger_adapter=logger,
        trace_adapter=trace,
    )

    summary = service.observability_summary()

    assert summary["event_bus"] == {"available": True, "event_count": 1}
    assert summary["subscribers"] == 3
    assert summary["adapters"] == {"metrics": True, "logger": True, "trace": True}
    assert summary["recent_events"][0]["correlation_id"] == "request-1"
