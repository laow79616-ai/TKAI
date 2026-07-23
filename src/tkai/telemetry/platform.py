"""Provider-neutral telemetry API layered compatibly over TelemetryManager."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import perf_counter
from typing import TYPE_CHECKING, Any, Protocol
from uuid import uuid4

from .context import CorrelationContext
from .models import Metric, MetricKind, TraceContext
from .sampling import AlwaysOnSampler, Sampler

if TYPE_CHECKING:
    from .manager import TelemetryManager


class SpanStatus(str, Enum):
    """Provider-neutral terminal status for a recorded span."""

    UNSET = "unset"
    OK = "ok"
    ERROR = "error"


class LogLevel(str, Enum):
    """Stable structured-log severity names independent of a logging package."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class TelemetryContext:
    """Immutable trace, span, and correlation identifiers for propagation."""

    trace_id: str | None = None
    span_id: str | None = None
    correlation_id: str | None = None

    def to_correlation_context(self) -> CorrelationContext:
        """Convert to the existing compatibility context model."""
        return CorrelationContext(
            trace_id=self.trace_id, correlation_id=self.correlation_id
        )


@dataclass(frozen=True, slots=True)
class Span:
    """Immutable trace span data with parent linkage and JSON-ready attributes."""

    trace_id: str
    span_id: str
    parent_span_id: str | None
    name: str
    started_at: datetime
    attributes: dict[str, object] = field(default_factory=dict)
    status: SpanStatus = SpanStatus.UNSET
    ended_at: datetime | None = None
    sampled: bool = True
    correlation_id: str | None = None

    @property
    def context(self) -> TelemetryContext:
        """Return propagation context for child spans and structured logs."""
        return TelemetryContext(self.trace_id, self.span_id, self.correlation_id)


@dataclass(frozen=True, slots=True)
class Trace:
    """A lightweight trace root used for diagnostics and external adapters."""

    trace_id: str
    root_span_id: str


class TelemetryProvider(Protocol):
    """Unified operations that future SDK-backed providers can implement."""

    def start_span(
        self,
        name: str,
        *,
        parent: TelemetryContext | None = None,
        attributes: dict[str, object] | None = None,
    ) -> Span: ...
    def end_span(self, span: Span, *, status: SpanStatus = SpanStatus.OK) -> Span: ...
    def counter(self, name: str, value: float = 1.0, **labels: str) -> Metric: ...
    def gauge(self, name: str, value: float, **labels: str) -> Metric: ...
    def histogram(self, name: str, value: float, **labels: str) -> Metric: ...


_current_context: ContextVar[TelemetryContext | None] = ContextVar(
    "tkai_telemetry_context", default=None
)


class TelemetryPlatform:
    """Explicit provider-neutral tracing, metrics, logs, and context propagation."""

    def __init__(
        self, manager: TelemetryManager, *, sampler: Sampler | None = None
    ) -> None:
        self.manager = manager
        self.sampler = sampler or AlwaysOnSampler()

    def current_context(self) -> TelemetryContext | None:
        """Return the current ContextVar value without creating a new trace."""
        return _current_context.get()

    @contextmanager
    def use_context(self, context: TelemetryContext) -> Iterator[TelemetryContext]:
        """Temporarily propagate explicit context and restore it after the block."""
        token = _current_context.set(context)
        try:
            yield context
        finally:
            _current_context.reset(token)

    def start_span(
        self,
        name: str,
        *,
        parent: TelemetryContext | None = None,
        attributes: dict[str, object] | None = None,
    ) -> Span:
        """Create one sampled or unsampled span without requiring an SDK."""
        inherited = parent or self.current_context()
        trace_id = (
            inherited.trace_id if inherited and inherited.trace_id else uuid4().hex
        )
        span = Span(
            trace_id,
            uuid4().hex,
            inherited.span_id if inherited else None,
            name,
            datetime.now(timezone.utc),
            {} if attributes is None else dict(attributes),
            sampled=self.sampler.should_sample(trace_id, name),
            correlation_id=inherited.correlation_id if inherited else None,
        )
        if span.sampled:
            self.manager.begin_span(
                name,
                attributes=span.attributes,
                trace_id=span.trace_id,
                span_id=span.span_id,
                parent_span_id=span.parent_span_id,
            )
        return span

    def end_span(self, span: Span, *, status: SpanStatus = SpanStatus.OK) -> Span:
        """Finish a span and export it only when its sampler accepted recording."""
        completed = Span(
            span.trace_id,
            span.span_id,
            span.parent_span_id,
            span.name,
            span.started_at,
            dict(span.attributes),
            status,
            datetime.now(timezone.utc),
            span.sampled,
            span.correlation_id,
        )
        if completed.sampled:
            self.manager.end_span(
                TraceContext(
                    completed.trace_id,
                    completed.span_id,
                    completed.parent_span_id,
                    completed.name,
                    completed.started_at,
                    attributes=completed.attributes,
                ),
                status=completed.status.value,
            )
        return completed

    @contextmanager
    def span(
        self, name: str, *, attributes: dict[str, object] | None = None
    ) -> Iterator[Span]:
        """Create a nested span scope and mark it failed if its block raises."""
        active = self.start_span(name, attributes=attributes)
        token: Token[TelemetryContext | None] = _current_context.set(active.context)
        try:
            yield active
        except Exception:
            self.end_span(active, status=SpanStatus.ERROR)
            raise
        else:
            self.end_span(active)
        finally:
            _current_context.reset(token)

    def counter(self, name: str, value: float = 1.0, **labels: str) -> Metric:
        """Record one provider-neutral counter through the compatible manager."""
        metric = Metric(name, value, labels=labels, kind=MetricKind.COUNTER)
        self.manager.record(metric)
        return metric

    def gauge(self, name: str, value: float, **labels: str) -> Metric:
        """Record one provider-neutral gauge through the compatible manager."""
        metric = Metric(name, value, labels=labels, kind=MetricKind.GAUGE)
        self.manager.record(metric)
        return metric

    def histogram(self, name: str, value: float, **labels: str) -> Metric:
        """Record one provider-neutral histogram through the compatible manager."""
        metric = Metric(name, value, labels=labels, kind=MetricKind.HISTOGRAM)
        self.manager.record(metric)
        return metric

    @contextmanager
    def timer(self, name: str, **labels: str) -> Iterator[None]:
        """Record elapsed milliseconds as a histogram after a caller's block."""
        started = perf_counter()
        try:
            yield
        finally:
            self.histogram(name, (perf_counter() - started) * 1000.0, **labels)

    def log(
        self,
        level: LogLevel | str,
        message: str,
        *,
        context: TelemetryContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> None:
        """Emit a structured log linked to explicit or currently propagated context."""
        active = context or self.current_context()
        correlation = active.to_correlation_context() if active else None
        self.manager.log(
            level.value if isinstance(level, LogLevel) else level,
            message,
            context=correlation,
            span_id=active.span_id if active else None,
            attributes=attributes,
        )
