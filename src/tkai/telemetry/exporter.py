"""Synchronous and asynchronous local-only telemetry exporter contract."""

from __future__ import annotations

import json
from collections.abc import Callable
from threading import RLock
from typing import Protocol

from .models import Metric, StructuredLog, TraceContext


class TelemetryExporter(Protocol):
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def export_metric(self, metric: Metric) -> None: ...
    def export_trace(self, trace: TraceContext) -> None: ...
    def export_log(self, log: StructuredLog) -> None: ...
    def health(self) -> bool: ...
    async def async_start(self) -> None: ...
    async def async_stop(self) -> None: ...
    async def async_export_metric(self, metric: Metric) -> None: ...
    async def async_export_trace(self, trace: TraceContext) -> None: ...
    async def async_export_log(self, log: StructuredLog) -> None: ...


class LocalExporter:
    """Thread-safe local exporter retaining telemetry only after explicit start."""

    def __init__(self) -> None:
        self._started = False
        self.metrics: list[Metric] = []
        self.traces: list[TraceContext] = []
        self.logs: list[StructuredLog] = []
        self._lock = RLock()

    def start(self) -> None:
        with self._lock:
            self._started = True

    def stop(self) -> None:
        with self._lock:
            self._started = False

    def export_metric(self, metric: Metric) -> None:
        with self._lock:
            if self._started:
                self.metrics.append(metric)

    def export_trace(self, trace: TraceContext) -> None:
        with self._lock:
            if self._started:
                self.traces.append(trace)

    def export_log(self, log: StructuredLog) -> None:
        with self._lock:
            if self._started:
                self.logs.append(log)

    def health(self) -> bool:
        with self._lock:
            return self._started

    async def async_start(self) -> None:
        self.start()

    async def async_stop(self) -> None:
        self.stop()

    async def async_export_metric(self, metric: Metric) -> None:
        self.export_metric(metric)

    async def async_export_trace(self, trace: TraceContext) -> None:
        self.export_trace(trace)

    async def async_export_log(self, log: StructuredLog) -> None:
        self.export_log(log)


class InMemoryExporter(LocalExporter):
    """Named compatibility-friendly exporter for deterministic offline inspection."""


class ConsoleExporter(InMemoryExporter):
    """Render telemetry JSON to an injected sink without binding logging libraries."""

    def __init__(self, sink: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self.sink = sink

    def export_metric(self, metric: Metric) -> None:
        super().export_metric(metric)
        self._emit({"metric": metric.to_dict()})

    def export_trace(self, trace: TraceContext) -> None:
        super().export_trace(trace)
        self._emit({"trace": trace.to_dict()})

    def export_log(self, log: StructuredLog) -> None:
        super().export_log(log)
        self._emit({"log": log.to_dict()})

    def _emit(self, payload: dict[str, object]) -> None:
        if self.sink is not None and self.health():
            self.sink(json.dumps(payload, ensure_ascii=False, sort_keys=True))


class PrometheusExporter(TelemetryExporter, Protocol):
    """Extension point for a future Prometheus exporter implementation."""


class OTLPExporter(TelemetryExporter, Protocol):
    """Extension point for a future OpenTelemetry Protocol exporter implementation."""
