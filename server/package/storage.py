"""Package storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Protocol

from .errors import PackageClosedError, PackageConflictError, PackageNotFoundError
from .models import (
    PackageEvent,
    PackageFilter,
    PackageQuery,
    PackageRecord,
    PackageSearchResult,
    PackageSort,
    PackageStatistics,
    PackageStatus,
)


class PackageStorage(Protocol):
    """Explicit local Package storage contract without persistence or transport."""

    def create(self, record: PackageRecord) -> PackageRecord: ...

    def update(self, record: PackageRecord) -> PackageRecord: ...

    def deprecate(self, package_id: str) -> PackageRecord: ...

    def withdraw(self, package_id: str) -> PackageRecord: ...

    def restore(self, package_id: str) -> PackageRecord: ...

    def delete(self, package_id: str) -> PackageRecord: ...

    def exists(self, package_id: str) -> bool: ...

    def get(self, package_id: str) -> PackageRecord: ...

    def list(self) -> tuple[PackageRecord, ...]: ...

    def search(self, query: PackageQuery) -> PackageSearchResult: ...

    def snapshot(self) -> tuple[PackageRecord, ...]: ...

    def statistics(self) -> PackageStatistics: ...

    def events(self) -> tuple[PackageEvent, ...]: ...

    def record_event(self, event: PackageEvent) -> None: ...

    def clear(self) -> tuple[PackageRecord, ...]: ...

    def close(self) -> None: ...


class ReferencePackageStorage:
    """Thread-safe in-memory Package storage with stable final snapshots."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, PackageRecord] = {}
        self._events: list[PackageEvent] = []
        self._closed = False

    def create(self, record: PackageRecord) -> PackageRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.package_id)
            if identifier in self._records:
                raise PackageConflictError("Package id already exists.")
            self._records[identifier] = record
            return record

    def update(self, record: PackageRecord) -> PackageRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.package_id)
            if identifier not in self._records:
                raise PackageNotFoundError(identifier)
            self._records[identifier] = record
            return record

    def deprecate(self, package_id: str) -> PackageRecord:
        return self._set_status(package_id, PackageStatus.DEPRECATED)

    def withdraw(self, package_id: str) -> PackageRecord:
        return self._set_status(package_id, PackageStatus.WITHDRAWN)

    def restore(self, package_id: str) -> PackageRecord:
        return self._set_status(package_id, PackageStatus.ACTIVE)

    def delete(self, package_id: str) -> PackageRecord:
        return self._set_status(package_id, PackageStatus.DELETED)

    def exists(self, package_id: str) -> bool:
        with self._lock:
            self._ensure_open()
            return package_id in self._records

    def get(self, package_id: str) -> PackageRecord:
        with self._lock:
            self._ensure_open()
            try:
                return self._records[package_id]
            except KeyError as exc:
                raise PackageNotFoundError(package_id) from exc

    def list(self) -> tuple[PackageRecord, ...]:
        with self._lock:
            self._ensure_open()
            return self._records_in_order()

    def search(self, query: PackageQuery) -> PackageSearchResult:
        with self._lock:
            self._ensure_open()
            records = [
                record
                for record in self._records_in_order()
                if self._matches(record, query.package_filter, query.keyword)
            ]
            records.sort(
                key=lambda record: self._sort_key(record, query.sort),
                reverse=query.descending,
            )
            return PackageSearchResult(tuple(records), len(records))

    def snapshot(self) -> tuple[PackageRecord, ...]:
        """Return final records even after close."""
        with self._lock:
            return self._records_in_order()

    def statistics(self) -> PackageStatistics:
        """Calculate current count-only statistics even after close."""
        with self._lock:
            records = self._records_in_order()
            return PackageStatistics(
                packages=len(records),
                active=sum(record.status is PackageStatus.ACTIVE for record in records),
                deprecated=sum(
                    record.status is PackageStatus.DEPRECATED for record in records
                ),
                withdrawn=sum(
                    record.status is PackageStatus.WITHDRAWN for record in records
                ),
                deleted=sum(
                    record.status is PackageStatus.DELETED for record in records
                ),
                categories=len(
                    {record.manifest.descriptor.category for record in records}
                ),
                versions=len({str(record.manifest.version) for record in records}),
                tags=len(
                    {
                        str(tag)
                        for record in records
                        for tag in record.manifest.descriptor.tags
                    }
                ),
            )

    def events(self) -> tuple[PackageEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def record_event(self, event: PackageEvent) -> None:
        with self._lock:
            self._events.append(event)

    def clear(self) -> tuple[PackageRecord, ...]:
        with self._lock:
            self._ensure_open()
            records = self._records_in_order()
            self._records.clear()
            return records

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _set_status(self, package_id: str, status: PackageStatus) -> PackageRecord:
        with self._lock:
            self._ensure_open()
            record = self.get(package_id)
            updated = replace(record, status=status)
            self._records[package_id] = updated
            return updated

    def _records_in_order(self) -> tuple[PackageRecord, ...]:
        return tuple(self._records[identifier] for identifier in sorted(self._records))

    def _ensure_open(self) -> None:
        if self._closed:
            raise PackageClosedError("Reference Package storage is closed.")

    @staticmethod
    def _matches(
        record: PackageRecord, package_filter: PackageFilter, keyword: str
    ) -> bool:
        descriptor = record.manifest.descriptor
        if (
            package_filter.publisher is not None
            and descriptor.publisher != package_filter.publisher
        ):
            return False
        if (
            package_filter.category is not None
            and descriptor.category is not package_filter.category
        ):
            return False
        if package_filter.tag is not None and not any(
            str(tag) == package_filter.tag for tag in descriptor.tags
        ):
            return False
        if (
            package_filter.version is not None
            and str(record.manifest.version) != package_filter.version
        ):
            return False
        if (
            package_filter.status is not None
            and record.status is not package_filter.status
        ):
            return False
        normalized = keyword.casefold()
        if not normalized:
            return True
        searchable = " ".join(
            (
                str(record.package_id),
                descriptor.publisher,
                descriptor.name,
                descriptor.description,
                str(record.manifest.version),
                *(str(tag) for tag in descriptor.tags),
            )
        ).casefold()
        return normalized in searchable

    @staticmethod
    def _sort_key(record: PackageRecord, sort: PackageSort) -> tuple[str, str]:
        descriptor = record.manifest.descriptor
        values = {
            PackageSort.PACKAGE_ID: str(record.package_id),
            PackageSort.PUBLISHER: descriptor.publisher,
            PackageSort.CATEGORY: descriptor.category.value,
            PackageSort.VERSION: str(record.manifest.version),
        }
        return (values[sort], str(record.package_id))
