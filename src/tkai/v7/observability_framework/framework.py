"""Local-only V7 observability collection, correlation, and diagnostics."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock
from typing import TypeVar, cast
from uuid import uuid4

from .contracts import (
    Alert,
    AuditCorrelation,
    DiagnosticResult,
    HealthRecord,
    HealthStatus,
    LogRecord,
    MetricDefinition,
    MetricSample,
    Observation,
    ObservationScope,
    Span,
    serialize,
)

T = TypeVar("T")


class ObservabilityError(RuntimeError):
    pass


class IsolationError(ObservabilityError):
    pass


class DuplicateReferenceError(ObservabilityError):
    pass


class ScopedStore:
    """Thread-safe local store whose reads always require an exact scope."""

    def __init__(self) -> None:
        self._items: list[object] = []
        self._lock = RLock()

    def add(self, value: T) -> T:
        with self._lock:
            self._items.append(value)
        return value

    def list(self, scope: ObservationScope) -> tuple[object, ...]:
        with self._lock:
            return tuple(
                item for item in self._items if getattr(item, "scope", None) == scope
            )


class MetricRegistry:
    def __init__(self) -> None:
        self._definitions: dict[tuple[ObservationScope, str], MetricDefinition] = {}
        self._samples = ScopedStore()
        self._lock = RLock()

    def register(self, definition: MetricDefinition) -> MetricDefinition:
        key = (definition.scope, definition.name)
        with self._lock:
            if key in self._definitions:
                raise DuplicateReferenceError(
                    f"metric already registered: {definition.name}"
                )
            self._definitions[key] = definition
        return definition

    def discover(self, scope: ObservationScope) -> tuple[MetricDefinition, ...]:
        return tuple(
            sorted(
                (
                    item
                    for (item_scope, _), item in self._definitions.items()
                    if item_scope == scope
                ),
                key=lambda item: item.name,
            )
        )

    def sample(self, sample: MetricSample) -> MetricSample:
        if (sample.scope, sample.metric_reference) not in self._definitions:
            raise ObservabilityError(f"unknown metric: {sample.metric_reference}")
        return self._samples.add(sample)

    def samples(self, scope: ObservationScope) -> tuple[MetricSample, ...]:
        return cast(tuple[MetricSample, ...], self._samples.list(scope))

    def aggregate(self, scope: ObservationScope) -> dict[str, float]:
        grouped: dict[str, list[float]] = {}
        for sample in self.samples(scope):
            grouped.setdefault(sample.metric_reference, []).append(sample.value)
        definitions = {item.name: item for item in self.discover(scope)}
        result: dict[str, float] = {}
        for name, values in grouped.items():
            mode = definitions[name].aggregation
            if mode == "sum":
                result[name] = sum(values)
            elif mode == "average":
                result[name] = sum(values) / len(values)
            elif mode == "min":
                result[name] = min(values)
            elif mode == "max":
                result[name] = max(values)
            else:
                result[name] = values[-1]
        return result


class ObservabilityFramework:
    """In-process, reference-only observability with no outbound transport."""

    def __init__(self) -> None:
        self.metrics = MetricRegistry()
        self.observations = ScopedStore()
        self.logs = ScopedStore()
        self.spans = ScopedStore()
        self.diagnostics = ScopedStore()
        self.health = ScopedStore()
        self.alerts = ScopedStore()
        self.correlations = ScopedStore()
        self.telemetry = ScopedStore()
        self.heartbeats = ScopedStore()
        self._diagnostic_collectors: dict[
            str, Callable[[ObservationScope], DiagnosticResult]
        ] = {}

    def observe(self, observation: Observation) -> Observation:
        return self.observations.add(observation)

    def log(self, record: LogRecord) -> LogRecord:
        self.logs.add(record)
        self.observe(
            Observation(
                observation_id=str(uuid4()),
                source="logging",
                category=record.classification,
                component=record.component,
                scope=record.scope,
                severity=record.severity,
                correlation_id=record.correlation_id,
                trace_id=record.trace_id,
                metadata=record.metadata,
            )
        )
        return record

    def trace(self, span: Span) -> Span:
        existing = {item.span_id for item in self.trace_spans(span.scope)}
        if span.span_id in existing:
            raise DuplicateReferenceError(f"span already registered: {span.span_id}")
        if span.parent_span_id and span.parent_span_id not in existing:
            raise ObservabilityError(f"unknown parent span: {span.parent_span_id}")
        return self.spans.add(span)

    def trace_spans(self, scope: ObservationScope) -> tuple[Span, ...]:
        return cast(tuple[Span, ...], self.spans.list(scope))

    def register_diagnostic(
        self, category: str, collector: Callable[[ObservationScope], DiagnosticResult]
    ) -> None:
        if category in self._diagnostic_collectors:
            raise DuplicateReferenceError(f"diagnostic already registered: {category}")
        self._diagnostic_collectors[category] = collector

    def run_diagnostics(
        self, scope: ObservationScope, categories: Iterable[str] | None = None
    ) -> tuple[DiagnosticResult, ...]:
        results: list[DiagnosticResult] = []
        for category in tuple(categories or self._diagnostic_collectors):
            if category not in self._diagnostic_collectors:
                raise ObservabilityError(f"unknown diagnostic: {category}")
            result = self._diagnostic_collectors[category](scope)
            if result.scope != scope or not result.read_only:
                raise IsolationError("diagnostics must be read-only and scope-bound")
            self.diagnostics.add(result)
            results.append(result)
        return tuple(results)

    def record_health(self, record: HealthRecord) -> HealthRecord:
        self.health.add(record)
        if record.kind == "heartbeat":
            self.heartbeats.add(record)
        return record

    def platform_health(self, scope: ObservationScope) -> dict[str, object]:
        records = cast(tuple[HealthRecord, ...], self.health.list(scope))
        rank = {
            HealthStatus.UNKNOWN: 0,
            HealthStatus.HEALTHY: 1,
            HealthStatus.DEGRADED: 2,
            HealthStatus.UNHEALTHY: 3,
        }
        status = (
            max((item.status for item in records), key=rank.__getitem__)
            if records
            else HealthStatus.UNKNOWN
        )
        return {
            "status": status.value,
            "liveness": any(item.kind == "liveness" for item in records),
            "readiness": any(
                item.kind == "readiness" and item.status == HealthStatus.HEALTHY
                for item in records
            ),
            "heartbeats": sum(item.kind == "heartbeat" for item in records),
            "dependencies": sum(item.kind == "dependency" for item in records),
            "framework": "healthy",
            "outbound_telemetry": False,
        }

    def record_telemetry(self, observation: Observation) -> Observation:
        if observation.source != "telemetry":
            raise ObservabilityError("telemetry source must be 'telemetry'")
        return self.telemetry.add(observation)

    def raise_alert(self, alert: Alert) -> Alert:
        return self.alerts.add(alert)

    def correlate(self, correlation: AuditCorrelation) -> AuditCorrelation:
        return self.correlations.add(correlation)

    def snapshot(self, scope: ObservationScope) -> dict[str, object]:
        return {
            "metrics": {
                "definitions": serialize(self.metrics.discover(scope)),
                "samples": serialize(self.metrics.samples(scope)),
                "aggregation": self.metrics.aggregate(scope),
            },
            "logging": serialize(self.logs.list(scope)),
            "tracing": serialize(self.spans.list(scope)),
            "diagnostics": serialize(self.diagnostics.list(scope)),
            "health": self.platform_health(scope),
            "alerts": serialize(self.alerts.list(scope)),
            "telemetry": serialize(self.telemetry.list(scope)),
            "audit": serialize(self.correlations.list(scope)),
        }


GLOBAL_OBSERVABILITY_FRAMEWORK = ObservabilityFramework()

__all__ = (
    "DuplicateReferenceError",
    "GLOBAL_OBSERVABILITY_FRAMEWORK",
    "IsolationError",
    "MetricRegistry",
    "ObservabilityError",
    "ObservabilityFramework",
    "ScopedStore",
)
