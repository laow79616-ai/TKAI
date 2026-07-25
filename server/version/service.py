"""Reference-only Version service with explicit local storage dependencies."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .errors import VersionClosedError, VersionStateError, VersionValidationError
from .models import (
    VersionEvent,
    VersionEventType,
    VersionId,
    VersionManifest,
    VersionQuery,
    VersionRecord,
    VersionSearchResult,
    VersionSnapshot,
    VersionStatistics,
    VersionStatus,
)
from .storage import ReferenceVersionStorage, VersionStorage


class ReferenceVersionService:
    """Pure-memory Version service with no Registry, Publisher, or Package access."""

    def __init__(self, storage: VersionStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferenceVersionStorage()
        self._lock = RLock()
        self._sequence = 0
        self._closed = False

    def create(self, record: VersionRecord) -> VersionRecord:
        """Create an explicitly supplied local Version record."""
        with self._lock:
            self._ensure_open()
            self._validate(record)
            created = self._storage.create(record)
            self._record(VersionEventType.CREATED, str(created.version_id))
            return created

    def update(self, version_id: str, manifest: VersionManifest) -> VersionRecord:
        """Replace a non-deleted Version manifest without artifact or release work."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(version_id)
            self._ensure_modifiable(current)
            updated = replace(current, manifest=manifest)
            self._validate(updated)
            result = self._storage.update(updated)
            self._record(VersionEventType.UPDATED, version_id)
            return result

    def deprecate(self, version_id: str) -> VersionRecord:
        """Set active or withdrawn Version records to deprecated."""
        return self._transition(
            version_id,
            allowed=(VersionStatus.ACTIVE, VersionStatus.WITHDRAWN),
            target=VersionStatus.DEPRECATED,
            event_type=VersionEventType.DEPRECATED,
        )

    def withdraw(self, version_id: str) -> VersionRecord:
        """Set active Version records to a descriptive withdrawn state."""
        return self._transition(
            version_id,
            allowed=(VersionStatus.ACTIVE,),
            target=VersionStatus.WITHDRAWN,
            event_type=VersionEventType.WITHDRAWN,
        )

    def restore(self, version_id: str) -> VersionRecord:
        """Restore withdrawn or deprecated Version records to active."""
        return self._transition(
            version_id,
            allowed=(VersionStatus.WITHDRAWN, VersionStatus.DEPRECATED),
            target=VersionStatus.ACTIVE,
            event_type=VersionEventType.RESTORED,
        )

    def delete(self, version_id: str) -> VersionRecord:
        """Set a descriptive deleted state without deleting any artifact."""
        return self._transition(
            version_id,
            allowed=(
                VersionStatus.ACTIVE,
                VersionStatus.WITHDRAWN,
                VersionStatus.DEPRECATED,
            ),
            target=VersionStatus.DELETED,
            event_type=VersionEventType.DELETED,
        )

    def get(self, version_id: str) -> VersionRecord:
        """Return one immutable local Version record."""
        with self._lock:
            self._ensure_open()
            return self._storage.get(version_id)

    def list(self) -> tuple[VersionRecord, ...]:
        """Return Version records in stable Version-id order."""
        with self._lock:
            self._ensure_open()
            return self._storage.list()

    def search(self, query: VersionQuery | None = None) -> VersionSearchResult:
        """Use deterministic local filtering only; no search engine is used."""
        with self._lock:
            self._ensure_open()
            return self._storage.search(query if query is not None else VersionQuery())

    def snapshot(self) -> VersionSnapshot:
        """Return an immutable final snapshot, including after idempotent close."""
        with self._lock:
            return VersionSnapshot(
                versions=self._storage.snapshot(),
                events=self._storage.events(),
                statistics=self._storage.statistics(),
                closed=self._closed,
            )

    def statistics(self) -> VersionStatistics:
        """Return fresh local statistics even after close."""
        with self._lock:
            return self._storage.statistics()

    def events(self) -> tuple[VersionEvent, ...]:
        """Return local events in deterministic strictly increasing sequence order."""
        with self._lock:
            return self._storage.events()

    def clear(self) -> tuple[VersionRecord, ...]:
        """Explicitly clear only this service's reference-memory Version records."""
        with self._lock:
            self._ensure_open()
            return self._storage.clear()

    def close(self) -> None:
        """Close idempotently; only final read-only state remains accessible."""
        with self._lock:
            if self._closed:
                return
            self._record(VersionEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _transition(
        self,
        version_id: str,
        *,
        allowed: tuple[VersionStatus, ...],
        target: VersionStatus,
        event_type: VersionEventType,
    ) -> VersionRecord:
        with self._lock:
            self._ensure_open()
            current = self._storage.get(version_id)
            if current.status is target:
                return current
            if current.status not in allowed:
                raise VersionStateError("Version lifecycle transition is not allowed.")
            methods = {
                VersionStatus.DEPRECATED: self._storage.deprecate,
                VersionStatus.WITHDRAWN: self._storage.withdraw,
                VersionStatus.ACTIVE: self._storage.restore,
                VersionStatus.DELETED: self._storage.delete,
            }
            transitioned = methods[target](version_id)
            self._record(event_type, version_id)
            return transitioned

    def _record(
        self, event_type: VersionEventType, version_id: str | None = None
    ) -> None:
        self._sequence += 1
        self._storage.record_event(
            VersionEvent(
                self._sequence,
                event_type,
                None if version_id is None else VersionId(version_id),
            )
        )

    @staticmethod
    def _ensure_modifiable(record: VersionRecord) -> None:
        if record.status is VersionStatus.DELETED:
            raise VersionStateError("Deleted Version records must not be modified.")

    @staticmethod
    def _validate(record: VersionRecord) -> None:
        if not record.manifest.descriptor.semantic_version:
            raise VersionValidationError("Version semantic version is required.")

    def _ensure_open(self) -> None:
        if self._closed:
            raise VersionClosedError("Reference Version service is closed.")
