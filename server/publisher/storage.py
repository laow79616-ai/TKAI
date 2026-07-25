"""Publisher storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock
from typing import Protocol

from .errors import PublisherClosedError, PublisherConflictError, PublisherNotFoundError
from .models import (
    PublisherCapability,
    PublisherQuery,
    PublisherRecord,
    PublisherSearchResult,
    PublisherSort,
    PublisherStatistics,
    PublisherStatus,
)


class PublisherStorage(Protocol):
    """Explicit local Publisher storage contract with no persistence requirement."""

    def create(self, record: PublisherRecord) -> PublisherRecord: ...

    def update(self, record: PublisherRecord) -> PublisherRecord: ...

    def suspend(self, publisher_id: str) -> PublisherRecord: ...

    def restore(self, publisher_id: str) -> PublisherRecord: ...

    def deprecate(self, publisher_id: str) -> PublisherRecord: ...

    def delete(self, publisher_id: str) -> PublisherRecord: ...

    def add_capability(
        self, publisher_id: str, capability: PublisherCapability
    ) -> PublisherRecord: ...

    def remove_capability(
        self, publisher_id: str, capability_name: str
    ) -> PublisherRecord: ...

    def exists(self, publisher_id: str) -> bool: ...

    def get(self, publisher_id: str) -> PublisherRecord: ...

    def list(self) -> tuple[PublisherRecord, ...]: ...

    def search(self, query: PublisherQuery) -> PublisherSearchResult: ...

    def snapshot(self) -> tuple[PublisherRecord, ...]: ...

    def statistics(self) -> PublisherStatistics: ...

    def clear(self) -> tuple[PublisherRecord, ...]: ...

    def close(self) -> None: ...


class ReferencePublisherStorage:
    """Thread-safe in-memory Publisher storage with final snapshots after close."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records: dict[str, PublisherRecord] = {}
        self._closed = False

    def create(self, record: PublisherRecord) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.publisher_id)
            if identifier in self._records:
                raise PublisherConflictError("Publisher id already exists.")
            self._records[identifier] = record
            return record

    def update(self, record: PublisherRecord) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            identifier = str(record.publisher_id)
            if identifier not in self._records:
                raise PublisherNotFoundError(identifier)
            self._records[identifier] = record
            return record

    def suspend(self, publisher_id: str) -> PublisherRecord:
        return self._set_status(publisher_id, PublisherStatus.SUSPENDED)

    def restore(self, publisher_id: str) -> PublisherRecord:
        return self._set_status(publisher_id, PublisherStatus.ACTIVE)

    def deprecate(self, publisher_id: str) -> PublisherRecord:
        return self._set_status(publisher_id, PublisherStatus.DEPRECATED)

    def delete(self, publisher_id: str) -> PublisherRecord:
        return self._set_status(publisher_id, PublisherStatus.DELETED)

    def add_capability(
        self, publisher_id: str, capability: PublisherCapability
    ) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            record = self.get(publisher_id)
            capabilities = frozenset((*record.descriptor.capabilities, capability))
            return self.update(
                replace(
                    record,
                    descriptor=replace(record.descriptor, capabilities=capabilities),
                )
            )

    def remove_capability(
        self, publisher_id: str, capability_name: str
    ) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            record = self.get(publisher_id)
            capabilities = frozenset(
                capability
                for capability in record.descriptor.capabilities
                if capability.name != capability_name
            )
            return self.update(
                replace(
                    record,
                    descriptor=replace(record.descriptor, capabilities=capabilities),
                )
            )

    def exists(self, publisher_id: str) -> bool:
        with self._lock:
            self._ensure_open()
            return publisher_id in self._records

    def get(self, publisher_id: str) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            try:
                return self._records[publisher_id]
            except KeyError as exc:
                raise PublisherNotFoundError(publisher_id) from exc

    def list(self) -> tuple[PublisherRecord, ...]:
        with self._lock:
            self._ensure_open()
            return self._records_in_order()

    def search(self, query: PublisherQuery) -> PublisherSearchResult:
        with self._lock:
            self._ensure_open()
            records = [
                record
                for record in self._records_in_order()
                if self._matches(record, query)
            ]
            records.sort(
                key=lambda record: self._sort_key(record, query.sort),
                reverse=query.descending,
            )
            return PublisherSearchResult(tuple(records), len(records))

    def snapshot(self) -> tuple[PublisherRecord, ...]:
        """Return the final immutable records even after close."""
        with self._lock:
            return self._records_in_order()

    def statistics(self) -> PublisherStatistics:
        """Calculate fresh count-only statistics even after close."""
        with self._lock:
            records = self._records_in_order()
            return PublisherStatistics(
                total_publishers=len(records),
                active=sum(
                    record.status is PublisherStatus.ACTIVE for record in records
                ),
                suspended=sum(
                    record.status is PublisherStatus.SUSPENDED for record in records
                ),
                deprecated=sum(
                    record.status is PublisherStatus.DEPRECATED for record in records
                ),
                deleted=sum(
                    record.status is PublisherStatus.DELETED for record in records
                ),
                community=sum(
                    record.descriptor.level.value == "community" for record in records
                ),
                verified=sum(
                    record.descriptor.level.value == "verified" for record in records
                ),
                official=sum(
                    record.descriptor.level.value == "official" for record in records
                ),
                enterprise=sum(
                    record.descriptor.level.value == "enterprise" for record in records
                ),
                organizations=len(
                    {
                        record.descriptor.organization.organization_id
                        for record in records
                        if record.descriptor.organization is not None
                    }
                ),
                capabilities=sum(
                    len(record.descriptor.capabilities) for record in records
                ),
            )

    def clear(self) -> tuple[PublisherRecord, ...]:
        with self._lock:
            self._ensure_open()
            records = self._records_in_order()
            self._records.clear()
            return records

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _set_status(
        self, publisher_id: str, status: PublisherStatus
    ) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            record = self.get(publisher_id)
            updated = replace(record, status=status)
            self._records[publisher_id] = updated
            return updated

    def _records_in_order(self) -> tuple[PublisherRecord, ...]:
        return tuple(self._records[identifier] for identifier in sorted(self._records))

    def _ensure_open(self) -> None:
        if self._closed:
            raise PublisherClosedError("Reference Publisher storage is closed.")

    @staticmethod
    def _matches(record: PublisherRecord, query: PublisherQuery) -> bool:
        publisher_filter = query.publisher_filter
        descriptor = record.descriptor
        organization = descriptor.organization
        if (
            publisher_filter.publisher_id is not None
            and str(record.publisher_id) != publisher_filter.publisher_id
        ):
            return False
        if (
            publisher_filter.name is not None
            and descriptor.profile.name != publisher_filter.name
        ):
            return False
        if publisher_filter.organization is not None and (
            organization is None
            or (
                organization.organization_id != publisher_filter.organization
                and organization.name != publisher_filter.organization
            )
        ):
            return False
        if (
            publisher_filter.level is not None
            and descriptor.level is not publisher_filter.level
        ):
            return False
        if (
            publisher_filter.status is not None
            and record.status is not publisher_filter.status
        ):
            return False
        if publisher_filter.capability is not None and not any(
            capability.name == publisher_filter.capability
            for capability in descriptor.capabilities
        ):
            return False
        keyword = query.keyword.casefold()
        if not keyword:
            return True
        searchable = " ".join(
            (
                str(record.publisher_id),
                descriptor.profile.name,
                descriptor.profile.description,
                "" if organization is None else organization.organization_id,
                "" if organization is None else organization.name,
                *(capability.name for capability in descriptor.capabilities),
            )
        ).casefold()
        return keyword in searchable

    @staticmethod
    def _sort_key(record: PublisherRecord, sort: PublisherSort) -> tuple[str, str]:
        values = {
            "publisher_id": str(record.publisher_id),
            "name": record.descriptor.profile.name,
            "level": record.descriptor.level.value,
            "status": record.status.value,
        }
        return (values[sort.value], str(record.publisher_id))
