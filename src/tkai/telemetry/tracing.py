"""Local trace span construction without a tracing SDK or exporter dependency."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from uuid import uuid4

from .models import TraceContext


class TraceRegistry:
    def __init__(self) -> None:
        self._traces: list[TraceContext] = []
        self._lock = RLock()

    def begin_span(
        self,
        operation: str,
        *,
        parent: TraceContext | None = None,
        attributes: dict[str, object] | None = None,
        trace_id: str | None = None,
        span_id: str | None = None,
        parent_span_id: str | None = None,
    ) -> TraceContext:
        trace = TraceContext(
            trace_id or (parent.trace_id if parent else uuid4().hex),
            span_id or uuid4().hex,
            (
                parent_span_id
                if parent_span_id is not None
                else (parent.span_id if parent else None)
            ),
            operation,
            datetime.now(timezone.utc),
            attributes={} if attributes is None else dict(attributes),
        )
        with self._lock:
            self._traces.append(trace)
        return trace

    def end_span(self, trace: TraceContext, *, status: str = "ok") -> TraceContext:
        finished = TraceContext(
            trace.trace_id,
            trace.span_id,
            trace.parent_span_id,
            trace.operation,
            trace.started_at,
            datetime.now(timezone.utc),
            status,
            trace.attributes,
        )
        with self._lock:
            self._traces.append(finished)
        return finished

    def snapshot(self) -> list[TraceContext]:
        with self._lock:
            return list(self._traces)
