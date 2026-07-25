"""Reference-only Statistics service with explicit local storage dependencies."""

from __future__ import annotations

from threading import RLock

from .errors import (
    StatisticsClosedError,
    StatisticsStateError,
)
from .models import (
    StatisticsCounters,
    StatisticsEvent,
    StatisticsEventType,
    StatisticsGroupBy,
    StatisticsQuery,
    StatisticsRecord,
    StatisticsResult,
    StatisticsSnapshot,
    StatisticsSource,
    StatisticsStatus,
    StatisticsSummary,
)
from .storage import ReferenceStatisticsStorage, StatisticsStorage


class ReferenceStatisticsService:
    """Pure-memory explicit Statistics service with on-demand aggregation only."""

    def __init__(self, storage: StatisticsStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferenceStatisticsStorage()
        self._lock = RLock()
        self._sequence = 0
        self._closed = False

    def register_source(self, source: StatisticsSource) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            registered = self._storage.register_source(source)
            self._record(
                StatisticsEventType.SOURCE_REGISTERED, source_id=source.source_id
            )
            return registered

    def update_source(self, source: StatisticsSource) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            current = self._storage.get_source(source.source_id)
            if current.status is StatisticsStatus.ARCHIVED:
                raise StatisticsStateError(
                    "Archived Statistics sources must be restored first."
                )
            updated = self._storage.update_source(source)
            self._record(StatisticsEventType.SOURCE_UPDATED, source_id=source.source_id)
            return updated

    def archive_source(self, source_id: str) -> StatisticsSource:
        return self._transition_source(
            source_id, StatisticsStatus.ARCHIVED, StatisticsEventType.SOURCE_ARCHIVED
        )

    def restore_source(self, source_id: str) -> StatisticsSource:
        return self._transition_source(
            source_id, StatisticsStatus.ACTIVE, StatisticsEventType.SOURCE_RESTORED
        )

    def get_source(self, source_id: str) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            return self._storage.get_source(source_id)

    def list_sources(self) -> tuple[StatisticsSource, ...]:
        with self._lock:
            self._ensure_open()
            return self._storage.list_sources()

    def record(self, record: StatisticsRecord) -> StatisticsRecord:
        with self._lock:
            self._ensure_open()
            saved = self._storage.record(record)
            self._record(
                StatisticsEventType.RECORD_ADDED,
                source_id=record.source_id,
                record_id=record.record_id,
                count=1,
            )
            return saved

    def record_many(
        self, records: tuple[StatisticsRecord, ...]
    ) -> tuple[StatisticsRecord, ...]:
        with self._lock:
            self._ensure_open()
            saved = self._storage.record_many(records)
            if saved:
                self._record(StatisticsEventType.RECORDS_ADDED, count=len(saved))
            return saved

    def get_record(self, record_id: str) -> StatisticsRecord:
        with self._lock:
            self._ensure_open()
            return self._storage.get_record(record_id)

    def list_records(self) -> tuple[StatisticsRecord, ...]:
        with self._lock:
            self._ensure_open()
            return self._storage.list_records()

    def query(self, query: StatisticsQuery | None = None) -> StatisticsResult:
        with self._lock:
            self._ensure_open()
            return self._storage.query(
                query if query is not None else StatisticsQuery()
            )

    def summarize(
        self,
        query: StatisticsQuery | None = None,
        group_by: StatisticsGroupBy | None = None,
        dimension_key: str | None = None,
    ) -> StatisticsSummary:
        """Delegate deterministic on-demand aggregation to the storage contract."""
        with self._lock:
            self._ensure_open()
            return self._storage.summarize(
                query if query is not None else StatisticsQuery(),
                group_by,
                dimension_key,
            )

    def counters(self) -> StatisticsCounters:
        with self._lock:
            return self._storage.counters()

    def snapshot(self) -> StatisticsSnapshot:
        with self._lock:
            return self._storage.snapshot()

    def events(self) -> tuple[StatisticsEvent, ...]:
        with self._lock:
            return self._storage.events()

    def clear(self) -> tuple[StatisticsSource, ...]:
        with self._lock:
            self._ensure_open()
            cleared = self._storage.clear()
            self._record(StatisticsEventType.CLEARED, count=len(cleared))
            return cleared

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._record(StatisticsEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _transition_source(
        self,
        source_id: str,
        target: StatisticsStatus,
        event_type: StatisticsEventType,
    ) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            current = self._storage.get_source(source_id)
            if current.status is target:
                return current
            if target is StatisticsStatus.ARCHIVED:
                updated = self._storage.archive_source(source_id)
            else:
                updated = self._storage.restore_source(source_id)
            self._record(event_type, source_id=source_id)
            return updated

    def _record(
        self,
        event_type: StatisticsEventType,
        source_id: str | None = None,
        record_id: str | None = None,
        count: int = 0,
    ) -> None:
        self._sequence += 1
        self._storage.record_event(
            StatisticsEvent(self._sequence, event_type, source_id, record_id, count)
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise StatisticsClosedError("Reference Statistics service is closed.")
