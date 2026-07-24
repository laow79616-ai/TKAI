"""Statistics storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Protocol

from .errors import (
    StatisticsAggregationError,
    StatisticsClosedError,
    StatisticsConflictError,
    StatisticsRecordNotFoundError,
    StatisticsSourceNotFoundError,
    StatisticsStateError,
)
from .models import (
    StatisticsCounters,
    StatisticsEvent,
    StatisticsFilter,
    StatisticsGroupBy,
    StatisticsMetricType,
    StatisticsQuery,
    StatisticsRecord,
    StatisticsResult,
    StatisticsSnapshot,
    StatisticsSort,
    StatisticsSource,
    StatisticsStatus,
    StatisticsSummary,
)


class StatisticsStorage(Protocol):
    """Explicit local Statistics storage contract without persistence or discovery."""

    def register_source(self, source: StatisticsSource) -> StatisticsSource: ...

    def update_source(self, source: StatisticsSource) -> StatisticsSource: ...

    def archive_source(self, source_id: str) -> StatisticsSource: ...

    def restore_source(self, source_id: str) -> StatisticsSource: ...

    def source_exists(self, source_id: str) -> bool: ...

    def get_source(self, source_id: str) -> StatisticsSource: ...

    def list_sources(self) -> tuple[StatisticsSource, ...]: ...

    def record(self, record: StatisticsRecord) -> StatisticsRecord: ...

    def record_many(
        self, records: tuple[StatisticsRecord, ...]
    ) -> tuple[StatisticsRecord, ...]: ...

    def get_record(self, record_id: str) -> StatisticsRecord: ...

    def list_records(self) -> tuple[StatisticsRecord, ...]: ...

    def query(self, query: StatisticsQuery) -> StatisticsResult: ...

    def summarize(
        self,
        query: StatisticsQuery,
        group_by: StatisticsGroupBy | None = None,
        dimension_key: str | None = None,
    ) -> StatisticsSummary: ...

    def counters(self) -> StatisticsCounters: ...

    def events(self) -> tuple[StatisticsEvent, ...]: ...

    def snapshot(self) -> StatisticsSnapshot: ...

    def record_event(self, event: StatisticsEvent) -> None: ...

    def clear(self) -> tuple[StatisticsSource, ...]: ...

    def close(self) -> None: ...


class ReferenceStatisticsStorage:
    """Thread-safe pure-memory Statistics storage with all-or-nothing batches."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._sources: dict[str, StatisticsSource] = {}
        self._records: dict[str, StatisticsRecord] = {}
        self._events: list[StatisticsEvent] = []
        self._closed = False

    def register_source(self, source: StatisticsSource) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            if source.source_id in self._sources:
                raise StatisticsConflictError("Statistics source id already exists.")
            self._sources[source.source_id] = source
            return source

    def update_source(self, source: StatisticsSource) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            if source.source_id not in self._sources:
                raise StatisticsSourceNotFoundError(source.source_id)
            self._sources[source.source_id] = source
            return source

    def archive_source(self, source_id: str) -> StatisticsSource:
        return self._set_source_status(source_id, StatisticsStatus.ARCHIVED)

    def restore_source(self, source_id: str) -> StatisticsSource:
        return self._set_source_status(source_id, StatisticsStatus.ACTIVE)

    def source_exists(self, source_id: str) -> bool:
        with self._lock:
            self._ensure_open()
            return source_id in self._sources

    def get_source(self, source_id: str) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            try:
                return self._sources[source_id]
            except KeyError as exc:
                raise StatisticsSourceNotFoundError(source_id) from exc

    def list_sources(self) -> tuple[StatisticsSource, ...]:
        with self._lock:
            self._ensure_open()
            return self._sources_in_order()

    def record(self, record: StatisticsRecord) -> StatisticsRecord:
        return self.record_many((record,))[0]

    def record_many(
        self, records: tuple[StatisticsRecord, ...]
    ) -> tuple[StatisticsRecord, ...]:
        with self._lock:
            self._ensure_open()
            self._validate_records(records)
            for record in records:
                self._records[record.record_id] = record
            return records

    def get_record(self, record_id: str) -> StatisticsRecord:
        with self._lock:
            self._ensure_open()
            try:
                return self._records[record_id]
            except KeyError as exc:
                raise StatisticsRecordNotFoundError(record_id) from exc

    def list_records(self) -> tuple[StatisticsRecord, ...]:
        with self._lock:
            self._ensure_open()
            return self._records_in_order()

    def query(self, query: StatisticsQuery) -> StatisticsResult:
        with self._lock:
            self._ensure_open()
            records = [
                record
                for record in self._records_in_order()
                if self._matches(record, query.statistics_filter)
            ]
            records.sort(
                key=lambda record: self._sort_key(record, query.sort),
                reverse=query.descending,
            )
            return StatisticsResult(
                tuple(records[query.offset : query.offset + query.limit]),
                len(records),
                query,
            )

    def summarize(
        self,
        query: StatisticsQuery,
        group_by: StatisticsGroupBy | None = None,
        dimension_key: str | None = None,
    ) -> StatisticsSummary:
        """Aggregate all records matching a query filter without pagination."""
        with self._lock:
            self._ensure_open()
            records = tuple(
                record
                for record in self._records_in_order()
                if self._matches(record, query.statistics_filter)
            )
            if not records:
                return StatisticsSummary()
            metric_names = {record.metric.name for record in records}
            metric_types = {record.metric.metric_type for record in records}
            if len(metric_names) != 1 or len(metric_types) != 1:
                raise StatisticsAggregationError(
                    "Statistics aggregation requires one compatible metric."
                )
            try:
                values = tuple(record.value.scalar() for record in records)
            except ValueError as exc:
                raise StatisticsAggregationError(
                    "Statistics aggregation requires scalar values."
                ) from exc
            total = sum(values)
            return StatisticsSummary(
                matching_records=len(records),
                source_count=len({record.source_id for record in records}),
                metric_count=len(metric_names),
                total=total,
                minimum=min(values),
                maximum=max(values),
                average=total / len(values),
                grouped_values=self._groups(records, group_by, dimension_key),
            )

    def counters(self) -> StatisticsCounters:
        """Calculate current source and record counters even after close."""
        with self._lock:
            sources = self._sources_in_order()
            records = self._records_in_order()
            return StatisticsCounters(
                total_sources=len(sources),
                active_sources=sum(
                    source.status is StatisticsStatus.ACTIVE for source in sources
                ),
                archived_sources=sum(
                    source.status is StatisticsStatus.ARCHIVED for source in sources
                ),
                total_records=len(records),
                metric_names=len({record.metric.name for record in records}),
                source_types=len({source.source_type for source in sources}),
                counters=sum(
                    record.metric.metric_type is StatisticsMetricType.COUNTER
                    for record in records
                ),
                gauges=sum(
                    record.metric.metric_type is StatisticsMetricType.GAUGE
                    for record in records
                ),
                distributions=sum(
                    record.metric.metric_type is StatisticsMetricType.DISTRIBUTION
                    for record in records
                ),
                summaries=sum(
                    record.metric.metric_type is StatisticsMetricType.SUMMARY
                    for record in records
                ),
            )

    def events(self) -> tuple[StatisticsEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def snapshot(self) -> StatisticsSnapshot:
        """Return a final safe snapshot, including after the storage is closed."""
        with self._lock:
            return StatisticsSnapshot(
                sources=self._sources_in_order(),
                records=self._records_in_order(),
                events=tuple(self._events),
                counters=self.counters(),
                closed=self._closed,
            )

    def record_event(self, event: StatisticsEvent) -> None:
        with self._lock:
            self._events.append(event)

    def clear(self) -> tuple[StatisticsSource, ...]:
        with self._lock:
            self._ensure_open()
            sources = self._sources_in_order()
            self._sources.clear()
            self._records.clear()
            return sources

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _set_source_status(
        self, source_id: str, status: StatisticsStatus
    ) -> StatisticsSource:
        with self._lock:
            self._ensure_open()
            source = self.get_source(source_id)
            updated = replace(source, status=status)
            self._sources[source_id] = updated
            return updated

    def _validate_records(self, records: tuple[StatisticsRecord, ...]) -> None:
        identifiers = {record.record_id for record in records}
        if len(identifiers) != len(records):
            raise StatisticsConflictError(
                "Statistics batch contains duplicate record ids."
            )
        for record in records:
            if record.record_id in self._records:
                raise StatisticsConflictError("Statistics record id already exists.")
            try:
                source = self._sources[record.source_id]
            except KeyError as exc:
                raise StatisticsSourceNotFoundError(record.source_id) from exc
            if source.status is not StatisticsStatus.ACTIVE:
                raise StatisticsStateError(
                    "Archived Statistics sources cannot accept records."
                )

    def _sources_in_order(self) -> tuple[StatisticsSource, ...]:
        return tuple(self._sources[identifier] for identifier in sorted(self._sources))

    def _records_in_order(self) -> tuple[StatisticsRecord, ...]:
        return tuple(self._records[identifier] for identifier in sorted(self._records))

    def _ensure_open(self) -> None:
        if self._closed:
            raise StatisticsClosedError("Reference Statistics storage is closed.")

    def _matches(
        self, record: StatisticsRecord, statistics_filter: StatisticsFilter
    ) -> bool:
        source = self._sources[record.source_id]
        if (
            statistics_filter.source_id is not None
            and record.source_id != statistics_filter.source_id
        ):
            return False
        if (
            statistics_filter.source_type is not None
            and source.source_type is not statistics_filter.source_type
        ):
            return False
        if (
            statistics_filter.metric_name is not None
            and record.metric.name != statistics_filter.metric_name
        ):
            return False
        if (
            statistics_filter.metric_type is not None
            and record.metric.metric_type is not statistics_filter.metric_type
        ):
            return False
        if (
            statistics_filter.record_id is not None
            and record.record_id != statistics_filter.record_id
        ):
            return False
        if (
            statistics_filter.status is not None
            and source.status is not statistics_filter.status
        ):
            return False
        if statistics_filter.dimension_key is not None:
            value = record.dimensions.values.get(statistics_filter.dimension_key)
            if value is None or (
                statistics_filter.dimension_value is not None
                and value != statistics_filter.dimension_value
            ):
                return False
        elif statistics_filter.dimension_value is not None:
            return False
        return True

    def _groups(
        self,
        records: tuple[StatisticsRecord, ...],
        group_by: StatisticsGroupBy | None,
        dimension_key: str | None,
    ) -> dict[str, int | float]:
        if group_by is None:
            return {}
        if group_by is StatisticsGroupBy.DIMENSION and not dimension_key:
            raise StatisticsAggregationError(
                "Dimension grouping requires a dimension key."
            )
        groups: dict[str, int | float] = {}
        for record in records:
            if group_by is StatisticsGroupBy.SOURCE:
                key = record.source_id
            elif group_by is StatisticsGroupBy.SOURCE_TYPE:
                key = self._sources[record.source_id].source_type.value
            elif group_by is StatisticsGroupBy.METRIC:
                key = record.metric.name
            else:
                assert dimension_key is not None
                key = record.dimensions.values.get(dimension_key, "")
            groups[key] = groups.get(key, 0) + record.value.scalar()
        return dict(sorted(groups.items()))

    @staticmethod
    def _sort_key(record: StatisticsRecord, sort: StatisticsSort) -> tuple[float, str]:
        values = {
            StatisticsSort.RECORD_ID: (0.0, record.record_id),
            StatisticsSort.SOURCE_ID: (0.0, record.source_id),
            StatisticsSort.METRIC_NAME: (0.0, record.metric.name),
            StatisticsSort.VALUE: (float(record.value.scalar()), record.record_id),
            StatisticsSort.SEQUENCE: (float(record.sequence), record.record_id),
        }
        return values[sort]
