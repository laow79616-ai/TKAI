"""Registry storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from threading import RLock
from typing import Protocol

from .errors import RegistryClosedError, RegistryConflictError, RegistryNotFoundError
from .models import RegistryEntry, RegistryId, RegistryStatistics, RegistryStatus


class RegistryStorage(Protocol):
    def create(self, entry: RegistryEntry) -> RegistryEntry: ...

    def update(self, entry: RegistryEntry) -> RegistryEntry: ...

    def delete(self, registry_id: RegistryId | str) -> RegistryEntry: ...

    def restore(self, entry: RegistryEntry) -> RegistryEntry: ...

    def exists(self, registry_id: RegistryId | str) -> bool: ...

    def get(self, registry_id: RegistryId | str) -> RegistryEntry: ...

    def list(self) -> tuple[RegistryEntry, ...]: ...

    def snapshot(self) -> tuple[RegistryEntry, ...]: ...

    def statistics(self) -> RegistryStatistics: ...

    def close(self) -> None: ...


class ReferenceRegistryStorage:
    """Thread-safe in-memory RegistryStorage with no database or filesystem use."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, RegistryEntry] = {}
        self._coordinates: dict[tuple[str, str, str], str] = {}
        self._closed = False

    def create(self, entry: RegistryEntry) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            identifier = str(entry.registry_id)
            coordinate = entry.descriptor.coordinate.key()
            if identifier in self._entries or coordinate in self._coordinates:
                raise RegistryConflictError(
                    "Registry entry or coordinate already exists."
                )
            self._entries[identifier] = entry
            self._coordinates[coordinate] = identifier
            return entry

    def update(self, entry: RegistryEntry) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            identifier = str(entry.registry_id)
            if identifier not in self._entries:
                raise RegistryNotFoundError(identifier)
            current = self._entries[identifier]
            if current.descriptor.coordinate != entry.descriptor.coordinate:
                raise RegistryConflictError("Registry coordinates cannot be changed.")
            self._entries[identifier] = entry
            return entry

    def delete(self, registry_id: RegistryId | str) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            identifier = str(registry_id)
            try:
                entry = self._entries[identifier]
            except KeyError as exc:
                raise RegistryNotFoundError(identifier) from exc
            deleted = RegistryEntry(
                registry_id=entry.registry_id,
                descriptor=entry.descriptor,
                status=RegistryStatus.DELETED,
            )
            self._entries[identifier] = deleted
            return deleted

    def restore(self, entry: RegistryEntry) -> RegistryEntry:
        return self.update(entry)

    def exists(self, registry_id: RegistryId | str) -> bool:
        with self._lock:
            self._ensure_open()
            return str(registry_id) in self._entries

    def get(self, registry_id: RegistryId | str) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            identifier = str(registry_id)
            try:
                return self._entries[identifier]
            except KeyError as exc:
                raise RegistryNotFoundError(identifier) from exc

    def list(self) -> tuple[RegistryEntry, ...]:
        with self._lock:
            self._ensure_open()
            return tuple(self._entries[key] for key in sorted(self._entries))

    def snapshot(self) -> tuple[RegistryEntry, ...]:
        return self.list()

    def statistics(self) -> RegistryStatistics:
        entries = self.list()
        return RegistryStatistics(
            entries=len(entries),
            active=sum(item.status is RegistryStatus.ACTIVE for item in entries),
            deprecated=sum(
                item.status is RegistryStatus.DEPRECATED for item in entries
            ),
            withdrawn=sum(item.status is RegistryStatus.WITHDRAWN for item in entries),
            deleted=sum(item.status is RegistryStatus.DELETED for item in entries),
            publishers=len({item.descriptor.coordinate.publisher for item in entries}),
            packages=len({item.descriptor.coordinate.package for item in entries}),
            versions=len({item.descriptor.coordinate.version for item in entries}),
        )

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RegistryClosedError("Reference registry storage is closed.")
