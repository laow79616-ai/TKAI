"""Version storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Protocol

from .errors import VersionClosedError, VersionConflictError, VersionNotFoundError
from .models import (
    VersionEvent,
    VersionFilter,
    VersionLabel,
    VersionQuery,
    VersionRecord,
    VersionSearchResult,
    VersionSort,
    VersionStatistics,
    VersionStatus,
)


class VersionStorage(Protocol):
    """Explicit local Version storage contract without persistence or transport."""

    def create(self, record: VersionRecord) -> VersionRecord: ...

    def update(self, record: VersionRecord) -> VersionRecord: ...

    def deprecate(self, version_id: str) -> VersionRecord: ...

    def withdraw(self, version_id: str) -> VersionRecord: ...

    def restore(self, version_id: str) -> VersionRecord: ...

    def delete(self, version_id: str) -> VersionRecord: ...

    def exists(self, version_id: str) -> bool: ...

    def get(self, version_id: str) -> VersionRecord: ...

    def list(self) -> tuple[VersionRecord, ...]: ...

    def search(self, query: VersionQuery) -> VersionSearchResult: ...

    def snapshot(self) -> tuple[VersionRecord, ...]: ...

    def statistics(self) -> VersionStatistics: ...

    def events(self) -> tuple[VersionEvent, ...]: ...

    def record_event(self, event: VersionEvent) -> None: ...

    def clear(self) -> tuple[VersionRecord, ...]: ...

    def close(self) -> None: ...


class ReferenceVersionStorage:
    """Thread-safe in-memory Version storage with stable final snapshots."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, VersionRecord] = {}
        self._events: list[VersionEvent] = []
        self._closed = False

    def create(self, record: VersionRecord) -> VersionRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.version_id)
            if identifier in self._records:
                raise VersionConflictError("Version id already exists.")
            self._records[identifier] = record
            return record

    def update(self, record: VersionRecord) -> VersionRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.version_id)
            if identifier not in self._records:
                raise VersionNotFoundError(identifier)
            self._records[identifier] = record
            return record

    def deprecate(self, version_id: str) -> VersionRecord:
        return self._set_status(version_id, VersionStatus.DEPRECATED)

    def withdraw(self, version_id: str) -> VersionRecord:
        return self._set_status(version_id, VersionStatus.WITHDRAWN)

    def restore(self, version_id: str) -> VersionRecord:
        return self._set_status(version_id, VersionStatus.ACTIVE)

    def delete(self, version_id: str) -> VersionRecord:
        return self._set_status(version_id, VersionStatus.DELETED)

    def exists(self, version_id: str) -> bool:
        with self._lock:
            self._ensure_open()
            return version_id in self._records

    def get(self, version_id: str) -> VersionRecord:
        with self._lock:
            self._ensure_open()
            try:
                return self._records[version_id]
            except KeyError as exc:
                raise VersionNotFoundError(version_id) from exc

    def list(self) -> tuple[VersionRecord, ...]:
        with self._lock:
            self._ensure_open()
            return self._records_in_order()

    def search(self, query: VersionQuery) -> VersionSearchResult:
        with self._lock:
            self._ensure_open()
            records = [
                record
                for record in self._records_in_order()
                if self._matches(record, query.version_filter, query.keyword)
            ]
            records.sort(
                key=lambda record: self._sort_key(record, query.sort),
                reverse=query.descending,
            )
            return VersionSearchResult(tuple(records), len(records))

    def snapshot(self) -> tuple[VersionRecord, ...]:
        """Return final records even after close."""
        with self._lock:
            return self._records_in_order()

    def statistics(self) -> VersionStatistics:
        """Calculate current count-only statistics even after close."""
        with self._lock:
            records = self._records_in_order()
            return VersionStatistics(
                versions=len(records),
                active=sum(record.status is VersionStatus.ACTIVE for record in records),
                deprecated=sum(
                    record.status is VersionStatus.DEPRECATED for record in records
                ),
                withdrawn=sum(
                    record.status is VersionStatus.WITHDRAWN for record in records
                ),
                deleted=sum(
                    record.status is VersionStatus.DELETED for record in records
                ),
                stable=sum(
                    record.manifest.descriptor.label is VersionLabel.STABLE
                    for record in records
                ),
                prerelease=sum(
                    record.manifest.descriptor.label is VersionLabel.PRERELEASE
                    for record in records
                ),
                beta=sum(
                    record.manifest.descriptor.label is VersionLabel.BETA
                    for record in records
                ),
                alpha=sum(
                    record.manifest.descriptor.label is VersionLabel.ALPHA
                    for record in records
                ),
            )

    def events(self) -> tuple[VersionEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def record_event(self, event: VersionEvent) -> None:
        with self._lock:
            self._events.append(event)

    def clear(self) -> tuple[VersionRecord, ...]:
        with self._lock:
            self._ensure_open()
            records = self._records_in_order()
            self._records.clear()
            return records

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _set_status(self, version_id: str, status: VersionStatus) -> VersionRecord:
        with self._lock:
            self._ensure_open()
            record = self.get(version_id)
            updated = replace(record, status=status)
            self._records[version_id] = updated
            return updated

    def _records_in_order(self) -> tuple[VersionRecord, ...]:
        return tuple(self._records[identifier] for identifier in sorted(self._records))

    def _ensure_open(self) -> None:
        if self._closed:
            raise VersionClosedError("Reference Version storage is closed.")

    @staticmethod
    def _matches(
        record: VersionRecord, version_filter: VersionFilter, keyword: str
    ) -> bool:
        descriptor = record.manifest.descriptor
        if (
            version_filter.package is not None
            and descriptor.package != version_filter.package
        ):
            return False
        if (
            version_filter.publisher is not None
            and descriptor.publisher != version_filter.publisher
        ):
            return False
        if (
            version_filter.semantic_version is not None
            and descriptor.semantic_version != version_filter.semantic_version
        ):
            return False
        if (
            version_filter.status is not None
            and record.status is not version_filter.status
        ):
            return False
        if (
            version_filter.label is not None
            and descriptor.label is not version_filter.label
        ):
            return False
        normalized = keyword.casefold()
        if not normalized:
            return True
        searchable = " ".join(
            (
                str(record.version_id),
                descriptor.package,
                descriptor.publisher,
                descriptor.semantic_version,
                descriptor.label.value,
                descriptor.description,
            )
        ).casefold()
        return normalized in searchable

    @staticmethod
    def _sort_key(record: VersionRecord, sort: VersionSort) -> tuple[str, str]:
        descriptor = record.manifest.descriptor
        values = {
            VersionSort.VERSION_ID: str(record.version_id),
            VersionSort.PACKAGE: descriptor.package,
            VersionSort.PUBLISHER: descriptor.publisher,
            VersionSort.SEMANTIC_VERSION: descriptor.semantic_version,
        }
        return (values[sort], str(record.version_id))
