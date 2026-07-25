"""Reference-only Registry domain service with explicit local dependencies."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .errors import RegistryClosedError, RegistryStateError, RegistryValidationError
from .models import (
    RegistryDescriptor,
    RegistryEntry,
    RegistryEvent,
    RegistryEventType,
    RegistryId,
    RegistryQuery,
    RegistrySearchResult,
    RegistrySnapshot,
    RegistrySort,
    RegistryStatistics,
    RegistryStatus,
)
from .storage import ReferenceRegistryStorage, RegistryStorage


class ReferenceRegistryService:
    """Pure-memory Registry service; it never starts a server or accesses a network."""

    def __init__(self, storage: RegistryStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferenceRegistryStorage()
        self._lock = RLock()
        self._events: list[RegistryEvent] = []
        self._sequence = 0
        self._closed = False

    def create(self, entry: RegistryEntry) -> RegistryEntry:
        """Create an explicit entry and record a deterministic event."""
        with self._lock:
            self._ensure_open()
            self._validate_entry(entry)
            created = self._storage.create(entry)
            self._record(RegistryEventType.CREATED, created.registry_id)
            return created

    def update(
        self, registry_id: RegistryId | str, descriptor: RegistryDescriptor
    ) -> RegistryEntry:
        """Replace entry descriptor data without changing its coordinate."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(registry_id)
            self._ensure_not_deleted(current)
            updated = replace(current, descriptor=descriptor)
            self._validate_entry(updated)
            result = self._storage.update(updated)
            self._record(RegistryEventType.UPDATED, result.registry_id)
            return result

    def deprecate(self, registry_id: RegistryId | str) -> RegistryEntry:
        """Set a non-deleted entry to its descriptive deprecated state."""
        return self._transition(
            registry_id, RegistryStatus.DEPRECATED, RegistryEventType.DEPRECATED
        )

    def withdraw(self, registry_id: RegistryId | str) -> RegistryEntry:
        """Set a non-deleted entry to its descriptive withdrawn state."""
        return self._transition(
            registry_id, RegistryStatus.WITHDRAWN, RegistryEventType.WITHDRAWN
        )

    def restore(self, registry_id: RegistryId | str) -> RegistryEntry:
        """Restore an inactive entry without external side effects."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(registry_id)
            if current.status is RegistryStatus.ACTIVE:
                raise RegistryStateError("An active Registry entry cannot be restored.")
            restored = self._storage.restore(
                replace(current, status=RegistryStatus.ACTIVE)
            )
            self._record(RegistryEventType.RESTORED, restored.registry_id)
            return restored

    def delete(self, registry_id: RegistryId | str) -> RegistryEntry:
        """Mark an entry deleted descriptively; no artifact is removed."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(registry_id)
            if current.status is RegistryStatus.DELETED:
                raise RegistryStateError(
                    "A deleted Registry entry cannot be deleted again."
                )
            deleted = self._storage.delete(registry_id)
            self._record(RegistryEventType.DELETED, deleted.registry_id)
            return deleted

    def get(self, registry_id: RegistryId | str) -> RegistryEntry:
        """Return an immutable entry by its explicit identifier."""
        with self._lock:
            self._ensure_open()
            return self._storage.get(registry_id)

    def list(self) -> tuple[RegistryEntry, ...]:
        """Return entries in stable identifier order."""
        with self._lock:
            self._ensure_open()
            return self._storage.list()

    def search(self, query: RegistryQuery | None = None) -> RegistrySearchResult:
        """Filter and sort local descriptions only; this is not a search engine."""
        with self._lock:
            self._ensure_open()
            query = query if query is not None else RegistryQuery()
            entries = [
                entry for entry in self._storage.list() if self._matches(entry, query)
            ]
            entries.sort(
                key=lambda entry: self._sort_key(entry, query.sort),
                reverse=query.descending,
            )
            return RegistrySearchResult(tuple(entries), len(entries))

    def snapshot(self) -> RegistrySnapshot:
        """Return a stable immutable snapshot and its deterministic snapshot event."""
        with self._lock:
            if not self._closed:
                self._record(RegistryEventType.SNAPSHOT)
            return RegistrySnapshot(
                entries=self._storage.snapshot(),
                events=tuple(self._events),
                statistics=self._storage.statistics(),
                closed=self._closed,
            )

    def statistics(self) -> RegistryStatistics:
        """Calculate fresh count-only statistics from reference storage."""
        with self._lock:
            return self._storage.statistics()

    def events(self) -> tuple[RegistryEvent, ...]:
        """Return deterministic local events in their insertion sequence."""
        with self._lock:
            return tuple(self._events)

    def clear(self) -> tuple[RegistryEntry, ...]:
        """Descriptively delete all remaining active entries in stable order."""
        with self._lock:
            self._ensure_open()
            deleted: list[RegistryEntry] = []
            for entry in self._storage.list():
                if entry.status is not RegistryStatus.DELETED:
                    deleted.append(self.delete(entry.registry_id))
            return tuple(deleted)

    def close(self) -> None:
        """Close this local service idempotently without starting cleanup workers."""
        with self._lock:
            if self._closed:
                return
            self._record(RegistryEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _transition(
        self,
        registry_id: RegistryId | str,
        status: RegistryStatus,
        event_type: RegistryEventType,
    ) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            current = self._storage.get(registry_id)
            self._ensure_not_deleted(current)
            if current.status is status:
                raise RegistryStateError(
                    "Registry entry is already in the requested state."
                )
            transitioned = self._storage.update(replace(current, status=status))
            self._record(event_type, transitioned.registry_id)
            return transitioned

    def _record(
        self, event_type: RegistryEventType, registry_id: RegistryId | None = None
    ) -> None:
        self._sequence += 1
        self._events.append(RegistryEvent(self._sequence, event_type, registry_id))

    def _ensure_open(self) -> None:
        if self._closed:
            raise RegistryClosedError("Reference Registry service is closed.")

    @staticmethod
    def _ensure_not_deleted(entry: RegistryEntry) -> None:
        if entry.status is RegistryStatus.DELETED:
            raise RegistryStateError("Deleted Registry entries must be restored first.")

    @staticmethod
    def _validate_entry(entry: RegistryEntry) -> None:
        if not entry.descriptor.title and not entry.descriptor.coordinate.package:
            raise RegistryValidationError("Registry entry requires a descriptor.")

    @staticmethod
    def _matches(entry: RegistryEntry, query: RegistryQuery) -> bool:
        registry_filter = query.registry_filter
        coordinate = entry.descriptor.coordinate
        if (
            registry_filter.publisher is not None
            and coordinate.publisher != registry_filter.publisher
        ):
            return False
        if (
            registry_filter.package is not None
            and coordinate.package != registry_filter.package
        ):
            return False
        if (
            registry_filter.version is not None
            and coordinate.version != registry_filter.version
        ):
            return False
        if (
            registry_filter.status is not None
            and entry.status is not registry_filter.status
        ):
            return False
        keyword = query.keyword.casefold()
        if not keyword:
            return True
        searchable = " ".join(
            (
                str(entry.registry_id),
                coordinate.publisher,
                coordinate.package,
                coordinate.version,
                entry.descriptor.title,
            )
        ).casefold()
        return keyword in searchable

    @staticmethod
    def _sort_key(entry: RegistryEntry, sort: RegistrySort) -> tuple[str, str]:
        coordinate = entry.descriptor.coordinate
        values = {
            RegistrySort.ENTRY_ID: str(entry.registry_id),
            RegistrySort.PUBLISHER: coordinate.publisher,
            RegistrySort.PACKAGE: coordinate.package,
            RegistrySort.VERSION: coordinate.version,
        }
        return (values[sort], str(entry.registry_id))
