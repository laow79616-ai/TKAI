"""Immutable EventBus events for explicit telemetry lifecycle and data."""

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True)
class TelemetryEvent(Event):
    subject: str = ""


@dataclass(frozen=True, slots=True)
class MetricRecorded(TelemetryEvent):
    name: str = field(default="MetricRecorded", init=False)


@dataclass(frozen=True, slots=True)
class TraceStarted(TelemetryEvent):
    name: str = field(default="TraceStarted", init=False)


@dataclass(frozen=True, slots=True)
class TraceFinished(TelemetryEvent):
    name: str = field(default="TraceFinished", init=False)


@dataclass(frozen=True, slots=True)
class TelemetryStarted(TelemetryEvent):
    name: str = field(default="TelemetryStarted", init=False)


@dataclass(frozen=True, slots=True)
class TelemetryStopped(TelemetryEvent):
    name: str = field(default="TelemetryStopped", init=False)


@dataclass(frozen=True, slots=True)
class ExporterRegistered(TelemetryEvent):
    name: str = field(default="ExporterRegistered", init=False)


@dataclass(frozen=True, slots=True)
class ExporterRemoved(TelemetryEvent):
    name: str = field(default="ExporterRemoved", init=False)
