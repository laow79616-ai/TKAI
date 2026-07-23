"""Explicit telemetry facade; LocalExporter is inert until start is called."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any

from tkai.observability import EventBus

from .context import CorrelationContext
from .events import (
    ExporterRegistered,
    ExporterRemoved,
    MetricRecorded,
    TelemetryEvent,
    TelemetryStarted,
    TelemetryStopped,
    TraceFinished,
    TraceStarted,
)
from .exporter import LocalExporter, TelemetryExporter
from .logging import TelemetryLoggingAdapter
from .metrics import MetricsRegistry
from .models import Metric, StructuredLog, TraceContext
from .registry import TelemetryRegistry
from .tracing import TraceRegistry


class TelemetryManager:
    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self.registry = TelemetryRegistry()
        self.metrics = MetricsRegistry()
        self.traces = TraceRegistry()
        self.logging = TelemetryLoggingAdapter()
        self.event_bus = event_bus
        self.events: list[TelemetryEvent] = []
        self._lock = RLock()
        self.registry.register("local", LocalExporter())

    def start(self, name: str = "local") -> None:
        self.registry.get(name).start()
        self._publish(TelemetryStarted(subject=name))

    def stop(self, name: str = "local") -> None:
        self.registry.get(name).stop()
        self._publish(TelemetryStopped(subject=name))

    def register_exporter(self, name: str, exporter: TelemetryExporter) -> None:
        self.registry.register(name, exporter)
        self._publish(ExporterRegistered(subject=name))

    def remove_exporter(self, name: str) -> TelemetryExporter:
        exporter = self.registry.remove(name)
        self._publish(ExporterRemoved(subject=name))
        return exporter

    def record(self, metric: Metric, *, exporter: str = "local") -> None:
        self.metrics.record(metric)
        self._export(exporter, lambda item: item.export_metric(metric))
        self._publish(MetricRecorded(subject=metric.name))

    def begin_span(
        self,
        operation: str,
        *,
        parent: TraceContext | None = None,
        attributes: dict[str, object] | None = None,
    ) -> TraceContext:
        trace = self.traces.begin_span(
            operation,
            parent=parent,
            attributes=attributes,
        )
        self._publish(TraceStarted(subject=trace.operation))
        return trace

    def end_span(self, trace: TraceContext, *, exporter: str = "local") -> TraceContext:
        finished = self.traces.end_span(trace)
        self._export(exporter, lambda item: item.export_trace(finished))
        self._publish(TraceFinished(subject=finished.operation))
        return finished

    def log(
        self,
        level: str,
        message: str,
        *,
        context: CorrelationContext | None = None,
        attributes: dict[str, Any] | None = None,
        exporter: str = "local",
    ) -> StructuredLog:
        record = self.logging.log(
            level,
            message,
            context=context,
            attributes=attributes,
        )
        self._export(exporter, lambda item: item.export_log(record))
        return record

    def summary(self) -> dict[str, object]:
        return {
            "exporters": [
                {"name": name, "healthy": exporter.health()}
                for name, exporter in self.registry.list()
            ],
            "metrics": len(self.metrics.snapshot()),
            "traces": len(self.traces.snapshot()),
            "logs": len(self.logging.records),
        }

    def _publish(self, event: TelemetryEvent) -> None:
        with self._lock:
            self.events.append(event)
        if self.event_bus is not None:
            try:
                self.event_bus.publish(event)
            except Exception:
                return

    def _export(
        self,
        name: str,
        operation: Callable[[TelemetryExporter], None],
    ) -> None:
        """Isolate optional exporter failures from local telemetry collection."""
        exporter = self.registry.get(name)
        try:
            operation(exporter)
        except Exception:
            return
