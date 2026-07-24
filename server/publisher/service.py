"""Reference-only Publisher domain service with explicit storage injection."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .errors import (
    PublisherClosedError,
    PublisherConflictError,
    PublisherNotFoundError,
    PublisherStateError,
    PublisherValidationError,
)
from .models import (
    PublisherCapability,
    PublisherDescriptor,
    PublisherEvent,
    PublisherEventType,
    PublisherId,
    PublisherQuery,
    PublisherRecord,
    PublisherSearchResult,
    PublisherSnapshot,
    PublisherStatistics,
    PublisherStatus,
)
from .storage import PublisherStorage, ReferencePublisherStorage


class ReferencePublisherService:
    """Pure-memory Publisher service; it never authenticates or creates accounts."""

    def __init__(self, storage: PublisherStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferencePublisherStorage()
        self._lock = RLock()
        self._events: list[PublisherEvent] = []
        self._sequence = 0
        self._closed = False

    def create(self, record: PublisherRecord) -> PublisherRecord:
        """Create an explicitly supplied local Publisher record."""
        with self._lock:
            self._ensure_open()
            self._validate(record)
            created = self._storage.create(record)
            self._record(PublisherEventType.CREATED, str(created.publisher_id))
            return created

    def update(
        self, publisher_id: str, descriptor: PublisherDescriptor
    ) -> PublisherRecord:
        """Replace a non-deleted Publisher descriptor with caller-provided data."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(publisher_id)
            self._ensure_modifiable(current)
            updated = replace(current, descriptor=descriptor)
            self._validate(updated)
            result = self._storage.update(updated)
            self._record(PublisherEventType.UPDATED, publisher_id)
            return result

    def suspend(self, publisher_id: str) -> PublisherRecord:
        """Move active Publisher records to suspended, idempotently."""
        return self._transition(
            publisher_id,
            allowed=(PublisherStatus.ACTIVE,),
            target=PublisherStatus.SUSPENDED,
            event_type=PublisherEventType.SUSPENDED,
        )

    def restore(self, publisher_id: str) -> PublisherRecord:
        """Restore suspended or deprecated Publisher records to active."""
        return self._transition(
            publisher_id,
            allowed=(PublisherStatus.SUSPENDED, PublisherStatus.DEPRECATED),
            target=PublisherStatus.ACTIVE,
            event_type=PublisherEventType.RESTORED,
        )

    def deprecate(self, publisher_id: str) -> PublisherRecord:
        """Mark active or suspended Publisher records as deprecated."""
        return self._transition(
            publisher_id,
            allowed=(PublisherStatus.ACTIVE, PublisherStatus.SUSPENDED),
            target=PublisherStatus.DEPRECATED,
            event_type=PublisherEventType.DEPRECATED,
        )

    def delete(self, publisher_id: str) -> PublisherRecord:
        """Set a descriptive deleted state without touching other domains."""
        return self._transition(
            publisher_id,
            allowed=(
                PublisherStatus.ACTIVE,
                PublisherStatus.SUSPENDED,
                PublisherStatus.DEPRECATED,
            ),
            target=PublisherStatus.DELETED,
            event_type=PublisherEventType.DELETED,
        )

    def add_capability(
        self, publisher_id: str, capability: PublisherCapability
    ) -> PublisherRecord:
        """Add one explicit descriptive capability without authorization effects."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(publisher_id)
            self._ensure_modifiable(current)
            if any(
                current_capability.name == capability.name
                for current_capability in current.descriptor.capabilities
            ):
                raise PublisherConflictError("Publisher capability already exists.")
            updated = self._storage.add_capability(publisher_id, capability)
            self._record(PublisherEventType.CAPABILITY_ADDED, publisher_id)
            return updated

    def remove_capability(
        self, publisher_id: str, capability_name: str
    ) -> PublisherRecord:
        """Remove one existing descriptive capability from a local Publisher."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(publisher_id)
            self._ensure_modifiable(current)
            if not any(
                capability.name == capability_name
                for capability in current.descriptor.capabilities
            ):
                raise PublisherNotFoundError(capability_name)
            updated = self._storage.remove_capability(publisher_id, capability_name)
            self._record(PublisherEventType.CAPABILITY_REMOVED, publisher_id)
            return updated

    def get(self, publisher_id: str) -> PublisherRecord:
        """Return a local immutable Publisher record."""
        with self._lock:
            self._ensure_open()
            return self._storage.get(publisher_id)

    def list(self) -> tuple[PublisherRecord, ...]:
        """Return local Publisher records in stable identifier order."""
        with self._lock:
            self._ensure_open()
            return self._storage.list()

    def search(self, query: PublisherQuery | None = None) -> PublisherSearchResult:
        """Use local deterministic filtering; no external search engine is used."""
        with self._lock:
            self._ensure_open()
            return self._storage.search(
                query if query is not None else PublisherQuery()
            )

    def snapshot(self) -> PublisherSnapshot:
        """Return a stable final snapshot; it remains readable after close."""
        with self._lock:
            return PublisherSnapshot(
                publishers=self._storage.snapshot(),
                events=tuple(self._events),
                statistics=self._storage.statistics(),
                closed=self._closed,
            )

    def statistics(self) -> PublisherStatistics:
        """Return fresh count-only statistics; they remain readable after close."""
        with self._lock:
            return self._storage.statistics()

    def events(self) -> tuple[PublisherEvent, ...]:
        """Return stable sequence-ordered local events."""
        with self._lock:
            return tuple(self._events)

    def clear(self) -> tuple[PublisherRecord, ...]:
        """Clear only local records and record one deterministic event."""
        with self._lock:
            self._ensure_open()
            cleared = self._storage.clear()
            if cleared:
                self._record(PublisherEventType.CLEARED)
            return cleared

    def close(self) -> None:
        """Close idempotently while retaining readable final snapshots."""
        with self._lock:
            if self._closed:
                return
            self._record(PublisherEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _transition(
        self,
        publisher_id: str,
        *,
        allowed: tuple[PublisherStatus, ...],
        target: PublisherStatus,
        event_type: PublisherEventType,
    ) -> PublisherRecord:
        with self._lock:
            self._ensure_open()
            current = self._storage.get(publisher_id)
            if current.status is target:
                return current
            if current.status not in allowed:
                raise PublisherStateError(
                    "Publisher lifecycle transition is not allowed."
                )
            methods = {
                PublisherStatus.SUSPENDED: self._storage.suspend,
                PublisherStatus.ACTIVE: self._storage.restore,
                PublisherStatus.DEPRECATED: self._storage.deprecate,
                PublisherStatus.DELETED: self._storage.delete,
            }
            transitioned = methods[target](publisher_id)
            self._record(event_type, publisher_id)
            return transitioned

    def _record(
        self, event_type: PublisherEventType, publisher_id: str | None = None
    ) -> None:
        self._sequence += 1
        self._events.append(
            PublisherEvent(
                self._sequence,
                event_type,
                None if publisher_id is None else PublisherId(publisher_id),
            )
        )

    @staticmethod
    def _ensure_modifiable(record: PublisherRecord) -> None:
        if record.status is PublisherStatus.DELETED:
            raise PublisherStateError("Deleted Publisher records must not be modified.")

    @staticmethod
    def _validate(record: PublisherRecord) -> None:
        if not record.descriptor.profile.name:
            raise PublisherValidationError("Publisher profile name is required.")

    def _ensure_open(self) -> None:
        if self._closed:
            raise PublisherClosedError("Reference Publisher service is closed.")
