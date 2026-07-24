"""Reference-only Package service with explicit local storage dependencies."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .errors import PackageClosedError, PackageStateError, PackageValidationError
from .models import (
    PackageEvent,
    PackageEventType,
    PackageId,
    PackageManifest,
    PackageQuery,
    PackageRecord,
    PackageSearchResult,
    PackageSnapshot,
    PackageStatistics,
    PackageStatus,
)
from .storage import PackageStorage, ReferencePackageStorage


class ReferencePackageService:
    """Pure-memory Package service; it never reads Registry or Publisher services."""

    def __init__(self, storage: PackageStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferencePackageStorage()
        self._lock = RLock()
        self._sequence = 0
        self._closed = False

    def create(self, record: PackageRecord) -> PackageRecord:
        """Create an explicitly supplied local Package description."""
        with self._lock:
            self._ensure_open()
            self._validate(record)
            created = self._storage.create(record)
            self._record(PackageEventType.CREATED, str(created.package_id))
            return created

    def update(self, package_id: str, manifest: PackageManifest) -> PackageRecord:
        """Replace a non-deleted Package manifest without resolving artifacts."""
        with self._lock:
            self._ensure_open()
            current = self._storage.get(package_id)
            self._ensure_modifiable(current)
            updated = replace(current, manifest=manifest)
            self._validate(updated)
            result = self._storage.update(updated)
            self._record(PackageEventType.UPDATED, package_id)
            return result

    def deprecate(self, package_id: str) -> PackageRecord:
        """Set an active or withdrawn Package description to deprecated."""
        return self._transition(
            package_id,
            allowed=(PackageStatus.ACTIVE, PackageStatus.WITHDRAWN),
            target=PackageStatus.DEPRECATED,
            event_type=PackageEventType.DEPRECATED,
        )

    def withdraw(self, package_id: str) -> PackageRecord:
        """Set an active Package description to withdrawn."""
        return self._transition(
            package_id,
            allowed=(PackageStatus.ACTIVE,),
            target=PackageStatus.WITHDRAWN,
            event_type=PackageEventType.WITHDRAWN,
        )

    def restore(self, package_id: str) -> PackageRecord:
        """Restore withdrawn or deprecated Package descriptions to active."""
        return self._transition(
            package_id,
            allowed=(PackageStatus.WITHDRAWN, PackageStatus.DEPRECATED),
            target=PackageStatus.ACTIVE,
            event_type=PackageEventType.RESTORED,
        )

    def delete(self, package_id: str) -> PackageRecord:
        """Set a descriptive deleted state without deleting an artifact."""
        return self._transition(
            package_id,
            allowed=(
                PackageStatus.ACTIVE,
                PackageStatus.WITHDRAWN,
                PackageStatus.DEPRECATED,
            ),
            target=PackageStatus.DELETED,
            event_type=PackageEventType.DELETED,
        )

    def get(self, package_id: str) -> PackageRecord:
        """Return one immutable local Package record."""
        with self._lock:
            self._ensure_open()
            return self._storage.get(package_id)

    def list(self) -> tuple[PackageRecord, ...]:
        """Return Package records in stable Package-id order."""
        with self._lock:
            self._ensure_open()
            return self._storage.list()

    def search(self, query: PackageQuery | None = None) -> PackageSearchResult:
        """Use deterministic local filtering only; no search engine is used."""
        with self._lock:
            self._ensure_open()
            return self._storage.search(query if query is not None else PackageQuery())

    def snapshot(self) -> PackageSnapshot:
        """Return an immutable final snapshot, including after idempotent close."""
        with self._lock:
            return PackageSnapshot(
                packages=self._storage.snapshot(),
                events=self._storage.events(),
                statistics=self._storage.statistics(),
                closed=self._closed,
            )

    def statistics(self) -> PackageStatistics:
        """Return fresh local statistics even after close."""
        with self._lock:
            return self._storage.statistics()

    def events(self) -> tuple[PackageEvent, ...]:
        """Return deterministic local events in strictly increasing sequence order."""
        with self._lock:
            return self._storage.events()

    def clear(self) -> tuple[PackageRecord, ...]:
        """Explicitly clear only this service's reference-memory Package records."""
        with self._lock:
            self._ensure_open()
            return self._storage.clear()

    def close(self) -> None:
        """Close idempotently; only final read-only state remains accessible."""
        with self._lock:
            if self._closed:
                return
            self._record(PackageEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _transition(
        self,
        package_id: str,
        *,
        allowed: tuple[PackageStatus, ...],
        target: PackageStatus,
        event_type: PackageEventType,
    ) -> PackageRecord:
        with self._lock:
            self._ensure_open()
            current = self._storage.get(package_id)
            if current.status is target:
                return current
            if current.status not in allowed:
                raise PackageStateError("Package lifecycle transition is not allowed.")
            methods = {
                PackageStatus.DEPRECATED: self._storage.deprecate,
                PackageStatus.WITHDRAWN: self._storage.withdraw,
                PackageStatus.ACTIVE: self._storage.restore,
                PackageStatus.DELETED: self._storage.delete,
            }
            transitioned = methods[target](package_id)
            self._record(event_type, package_id)
            return transitioned

    def _record(
        self, event_type: PackageEventType, package_id: str | None = None
    ) -> None:
        self._sequence += 1
        self._storage.record_event(
            PackageEvent(
                self._sequence,
                event_type,
                None if package_id is None else PackageId(package_id),
            )
        )

    @staticmethod
    def _ensure_modifiable(record: PackageRecord) -> None:
        if record.status is PackageStatus.DELETED:
            raise PackageStateError("Deleted Package records must not be modified.")

    @staticmethod
    def _validate(record: PackageRecord) -> None:
        if not record.manifest.descriptor.name:
            raise PackageValidationError("Package name is required.")

    def _ensure_open(self) -> None:
        if self._closed:
            raise PackageClosedError("Reference Package service is closed.")
