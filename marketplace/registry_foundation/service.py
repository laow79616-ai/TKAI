"""Thread-safe, local-only Registry Foundation reference service."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from threading import RLock

from ..publication import PublicationSnapshot
from .contracts import RegistryPublicationAdapter
from .errors import (
    RegistryClosedError,
    RegistryConflictError,
    RegistryNotFoundError,
)
from .models import (
    RegistryCoordinate,
    RegistryEntry,
    RegistryEntryId,
    RegistryEvent,
    RegistryEventType,
    RegistryFilter,
    RegistryIndex,
    RegistryMetadata,
    RegistryQuery,
    RegistrySearchResult,
    RegistrySnapshot,
    RegistrySort,
    RegistryStatistics,
    RegistryStatus,
)


class ReferenceRegistryService:
    """A bounded-caller-owned local registry with no remote state or background work."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._entries: dict[str, RegistryEntry] = {}
        self._coordinates: dict[tuple[str, str, str], str] = {}
        self._events: list[RegistryEvent] = []
        self._sequence = 0
        self._closed = False

    def register(self, entry: RegistryEntry) -> RegistryEntry:
        """Store a caller-owned entry, rejecting duplicate ids and coordinates."""
        with self._lock:
            self._ensure_open()
            entry_id = str(entry.entry_id)
            coordinate = entry.coordinate.key()
            if entry_id in self._entries:
                raise RegistryConflictError(
                    f"Registry entry already exists: {entry_id}."
                )
            if coordinate in self._coordinates:
                raise RegistryConflictError(
                    "Registry coordinate already exists: " + "/".join(coordinate) + "."
                )
            self._entries[entry_id] = entry
            self._coordinates[coordinate] = entry_id
            self._emit(RegistryEventType.REGISTERED, entry)
            return entry

    def register_publication(
        self,
        entry_id: RegistryEntryId,
        snapshot: PublicationSnapshot,
        adapter: RegistryPublicationAdapter,
        metadata: RegistryMetadata | None = None,
    ) -> RegistryEntry:
        """Register one explicitly supplied accepted publication through an adapter."""
        return self.register(adapter.entry_from_snapshot(entry_id, snapshot, metadata))

    def unregister(self, entry_id: RegistryEntryId | str) -> RegistryEntry:
        """Remove an entry and its local coordinate index."""
        with self._lock:
            self._ensure_open()
            key = str(entry_id)
            entry = self._entries.pop(key, None)
            if entry is None:
                raise RegistryNotFoundError(f"Registry entry was not found: {key}.")
            self._coordinates.pop(entry.coordinate.key(), None)
            self._emit(RegistryEventType.UNREGISTERED, entry)
            return entry

    def withdraw(self, entry_id: RegistryEntryId | str) -> RegistryEntry:
        """Mark an entry withdrawn without deleting its descriptive history."""
        return self._set_status(
            entry_id, RegistryStatus.WITHDRAWN, RegistryEventType.WITHDRAWN
        )

    def deprecate(self, entry_id: RegistryEntryId | str) -> RegistryEntry:
        """Mark an entry deprecated without selecting a replacement package."""
        return self._set_status(
            entry_id, RegistryStatus.DEPRECATED, RegistryEventType.DEPRECATED
        )

    def restore(self, entry_id: RegistryEntryId | str) -> RegistryEntry:
        """Restore an entry to descriptive active status."""
        return self._set_status(
            entry_id, RegistryStatus.ACTIVE, RegistryEventType.RESTORED
        )

    def get(self, entry_id: RegistryEntryId | str) -> RegistryEntry:
        """Return one immutable entry by explicit id."""
        with self._lock:
            self._ensure_open()
            key = str(entry_id)
            try:
                return self._entries[key]
            except KeyError as exc:
                raise RegistryNotFoundError(
                    f"Registry entry was not found: {key}."
                ) from exc

    def get_by_coordinate(self, coordinate: RegistryCoordinate) -> RegistryEntry:
        """Return an entry by exact publisher/package/version coordinate."""
        with self._lock:
            self._ensure_open()
            entry_id = self._coordinates.get(coordinate.key())
            if entry_id is None:
                raise RegistryNotFoundError("Registry coordinate was not found.")
            return self._entries[entry_id]

    def exists(self, entry_id: RegistryEntryId | str) -> bool:
        """Return whether an entry id is currently present."""
        with self._lock:
            self._ensure_open()
            return str(entry_id) in self._entries

    def list(self) -> tuple[RegistryEntry, ...]:
        """Return entries in stable entry-id order."""
        with self._lock:
            self._ensure_open()
            return self._ordered_entries()

    def filter(self, registry_filter: RegistryFilter) -> tuple[RegistryEntry, ...]:
        """Return a stable filtered immutable entry tuple."""
        with self._lock:
            self._ensure_open()
            return tuple(
                entry
                for entry in self._ordered_entries()
                if self._matches_filter(entry, registry_filter)
            )

    def search(self, query: RegistryQuery | None = None) -> RegistrySearchResult:
        """Search descriptive fields and apply stable caller-selected sorting."""
        with self._lock:
            self._ensure_open()
            query = RegistryQuery() if query is None else query
            entries = [
                entry
                for entry in self._ordered_entries()
                if self._matches_filter(entry, query.registry_filter)
                and self._matches_keyword(entry, query.keyword)
            ]
            entries.sort(
                key=lambda entry: self._sort_key(entry, query.sort),
                reverse=query.descending,
            )
            return RegistrySearchResult(entries=tuple(entries), total=len(entries))

    def snapshot(self) -> RegistrySnapshot:
        """Return a defensive immutable snapshot and derived local index."""
        with self._lock:
            self._ensure_open()
            entries = self._ordered_entries()
            return RegistrySnapshot(entries=entries, index=self._build_index(entries))

    def statistics(self) -> RegistryStatistics:
        """Return deterministic local statistics with no performance claims."""
        with self._lock:
            self._ensure_open()
            entries = self._ordered_entries()
            return RegistryStatistics(
                total_entries=len(entries),
                active_entries=sum(
                    entry.status is RegistryStatus.ACTIVE for entry in entries
                ),
                withdrawn_entries=sum(
                    entry.status is RegistryStatus.WITHDRAWN for entry in entries
                ),
                deprecated_entries=sum(
                    entry.status is RegistryStatus.DEPRECATED for entry in entries
                ),
                publishers=len({entry.publisher.publisher_id for entry in entries}),
                packages=len({entry.package_manifest.package_id for entry in entries}),
                versions=len(
                    {str(entry.package_manifest.version) for entry in entries}
                ),
                categories=len({entry.category for entry in entries}),
            )

    def events(self) -> tuple[RegistryEvent, ...]:
        """Return the local event history in increasing sequence order."""
        with self._lock:
            return tuple(self._events)

    def clear(self) -> None:
        """Clear all entries; repeated clearing is an idempotent no-op."""
        with self._lock:
            self._ensure_open()
            if not self._entries:
                return
            self._entries.clear()
            self._coordinates.clear()
            self._emit(RegistryEventType.CLEARED, None)

    def close(self) -> None:
        """Close the local service; repeated closing is an idempotent no-op."""
        with self._lock:
            if self._closed:
                return
            self._entries.clear()
            self._coordinates.clear()
            self._closed = True
            self._emit(RegistryEventType.CLOSED, None)

    def _set_status(
        self,
        entry_id: RegistryEntryId | str,
        status: RegistryStatus,
        event_type: RegistryEventType,
    ) -> RegistryEntry:
        with self._lock:
            self._ensure_open()
            key = str(entry_id)
            try:
                current = self._entries[key]
            except KeyError as exc:
                raise RegistryNotFoundError(
                    f"Registry entry was not found: {key}."
                ) from exc
            if current.status is status:
                return current
            entry = replace(current, status=status)
            self._entries[key] = entry
            self._emit(event_type, entry)
            return entry

    def _ensure_open(self) -> None:
        if self._closed:
            raise RegistryClosedError("Registry service is closed.")

    def _emit(self, event_type: RegistryEventType, entry: RegistryEntry | None) -> None:
        self._sequence += 1
        self._events.append(
            RegistryEvent(
                sequence=self._sequence,
                event_type=event_type,
                entry_id=None if entry is None else entry.entry_id,
                coordinate=None if entry is None else entry.coordinate,
            )
        )

    def _ordered_entries(self) -> tuple[RegistryEntry, ...]:
        return tuple(self._entries[key] for key in sorted(self._entries))

    @staticmethod
    def _matches_filter(entry: RegistryEntry, registry_filter: RegistryFilter) -> bool:
        return all(
            (
                registry_filter.publisher_id is None
                or entry.publisher.publisher_id == registry_filter.publisher_id,
                registry_filter.package_id is None
                or entry.package_manifest.package_id == registry_filter.package_id,
                registry_filter.category is None
                or entry.category is registry_filter.category,
                registry_filter.version is None
                or entry.package_manifest.version == registry_filter.version,
                registry_filter.tag is None or registry_filter.tag in entry.tags,
                registry_filter.status is None
                or entry.status is registry_filter.status,
            )
        )

    @staticmethod
    def _matches_keyword(entry: RegistryEntry, keyword: str | None) -> bool:
        if keyword is None or not keyword.strip():
            return True
        normalized = keyword.casefold()
        fields = (
            entry.package_manifest.package_id,
            entry.package_manifest.name,
            entry.package_manifest.description,
            entry.publisher.publisher_id,
            *(tag.value for tag in entry.tags),
        )
        return any(normalized in value.casefold() for value in fields)

    @staticmethod
    def _sort_key(entry: RegistryEntry, sort: RegistrySort) -> tuple[str, str]:
        primary = {
            RegistrySort.PACKAGE_ID: entry.package_manifest.package_id,
            RegistrySort.PUBLISHER_ID: entry.publisher.publisher_id,
            RegistrySort.VERSION: str(entry.package_manifest.version),
            RegistrySort.CATEGORY: entry.category.value,
            RegistrySort.STATUS: entry.status.value,
        }[sort]
        return (primary, str(entry.entry_id))

    @staticmethod
    def _build_index(entries: tuple[RegistryEntry, ...]) -> RegistryIndex:
        package_ids: defaultdict[str, list[str]] = defaultdict(list)
        publisher_ids: defaultdict[str, list[str]] = defaultdict(list)
        categories: defaultdict[str, list[str]] = defaultdict(list)
        versions: defaultdict[str, list[str]] = defaultdict(list)
        tags: defaultdict[str, list[str]] = defaultdict(list)
        statuses: defaultdict[str, list[str]] = defaultdict(list)
        coordinates: dict[tuple[str, str, str], str] = {}
        for entry in entries:
            entry_id = str(entry.entry_id)
            coordinates[entry.coordinate.key()] = entry_id
            package_ids[entry.package_manifest.package_id].append(entry_id)
            publisher_ids[entry.publisher.publisher_id].append(entry_id)
            categories[entry.category.value].append(entry_id)
            versions[str(entry.package_manifest.version)].append(entry_id)
            statuses[entry.status.value].append(entry_id)
            for tag in entry.tags:
                tags[tag.value].append(entry_id)
        return RegistryIndex(
            coordinates=coordinates,
            package_ids={key: tuple(value) for key, value in package_ids.items()},
            publisher_ids={key: tuple(value) for key, value in publisher_ids.items()},
            categories={key: tuple(value) for key, value in categories.items()},
            versions={key: tuple(value) for key, value in versions.items()},
            tags={key: tuple(sorted(value)) for key, value in tags.items()},
            statuses={key: tuple(value) for key, value in statuses.items()},
        )
