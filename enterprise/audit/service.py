"""Explicit Audit service contract and bounded in-memory reference implementation."""

from __future__ import annotations

from threading import RLock
from typing import Protocol

from .errors import (
    AuditCapacityError,
    AuditClosedError,
    AuditConflictError,
    AuditNotFoundError,
)
from .models import AuditEvent, AuditQuery, AuditQueryResult, AuditSort
from .redaction import AuditRedactionPolicy, AuditRedactor, RedactionResult


class AuditService(Protocol):
    def record(self, event: AuditEvent) -> None: ...
    def record_many(self, events: tuple[AuditEvent, ...]) -> None: ...
    def query(self, query: AuditQuery) -> AuditQueryResult: ...
    def get(self, event_id: str) -> AuditEvent: ...
    def redact(
        self, event: AuditEvent, policy: AuditRedactionPolicy
    ) -> RedactionResult: ...
    def snapshot(self) -> tuple[AuditEvent, ...]: ...
    def close(self) -> None: ...


class ReferenceAuditService:
    """Thread-safe, bounded, reference-only service with no exporter or persistence."""

    def __init__(self, capacity: int = 1000, overflow: str = "reject") -> None:
        if capacity < 1 or overflow not in {"reject", "evict_oldest"}:
            raise ValueError("Audit capacity and overflow policy are invalid.")
        self._capacity, self._overflow = capacity, overflow
        self._events: dict[str, AuditEvent] = {}
        self._closed = False
        self._lock = RLock()
        self._redactor = AuditRedactor()

    def _open(self) -> None:
        if self._closed:
            raise AuditClosedError("Reference audit service is closed.")

    def record(self, event: AuditEvent) -> None:
        with self._lock:
            self._open()
            if event.event_id in self._events:
                raise AuditConflictError(
                    f"Audit event {event.event_id!r} is duplicate."
                )
            if len(self._events) >= self._capacity:
                if self._overflow == "reject":
                    raise AuditCapacityError("Reference audit capacity is full.")
                oldest = self._ordered()[0].event_id
                del self._events[oldest]
            self._events[event.event_id] = event

    def record_many(self, events: tuple[AuditEvent, ...]) -> None:
        for event in events:
            self.record(event)

    def _ordered(self) -> tuple[AuditEvent, ...]:
        return tuple(
            sorted(
                self._events.values(), key=lambda item: (item.timestamp, item.event_id)
            )
        )

    def get(self, event_id: str) -> AuditEvent:
        with self._lock:
            self._open()
            try:
                return self._events[event_id]
            except KeyError as exc:
                raise AuditNotFoundError(
                    f"Audit event {event_id!r} was not found."
                ) from exc

    def query(self, query: AuditQuery) -> AuditQueryResult:
        with self._lock:
            self._open()
            events = [event for event in self._ordered() if self._matches(event, query)]
            if query.sort is AuditSort.DESCENDING:
                events.reverse()
            total = len(events)
            selected = tuple(
                events[query.page.offset : query.page.offset + query.page.limit]
            )
            cursor = (
                str(query.page.offset + len(selected))
                if query.page.offset + len(selected) < total
                else None
            )
            return AuditQueryResult(selected, total, cursor)

    @staticmethod
    def _matches(event: AuditEvent, query: AuditQuery) -> bool:
        checks = (
            (query.event_id, event.event_id),
            (query.actor_id, event.actor.actor_id),
            (query.target_id, event.target.target_id),
            (query.action, event.action),
            (query.tenant_id, event.context.tenant_id),
            (query.organization_id, event.context.organization_id),
            (query.request_id, event.context.request_id),
            (query.correlation_id, event.context.correlation_id),
        )
        if any(
            expected is not None and expected != actual for expected, actual in checks
        ):
            return False
        if query.category is not None and query.category is not event.category:
            return False
        if (
            query.outcome_status is not None
            and query.outcome_status is not event.outcome.status
        ):
            return False
        if query.start_at is not None and event.timestamp < query.start_at:
            return False
        if query.end_at is not None and event.timestamp > query.end_at:
            return False
        if (
            query.metadata_key is not None
            and event.metadata.get(query.metadata_key) != query.metadata_value
        ):
            return False
        return True

    def redact(
        self, event: AuditEvent, policy: AuditRedactionPolicy
    ) -> RedactionResult:
        return self._redactor.redact(event, policy)

    def snapshot(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return self._ordered()

    def close(self) -> None:
        with self._lock:
            self._closed = True
