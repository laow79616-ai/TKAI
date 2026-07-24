"""Reference-only Search service with explicit local storage dependencies."""

from __future__ import annotations

from threading import RLock

from .errors import SearchClosedError
from .models import (
    SearchEvent,
    SearchEventType,
    SearchQuery,
    SearchResult,
    SearchSnapshot,
    SearchStatistics,
)
from .storage import ReferenceSearchStorage, SearchStorage


class ReferenceSearchService:
    """Pure-memory unified query service; it never reads or mutates other domains."""

    def __init__(self, storage: SearchStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferenceSearchStorage()
        self._lock = RLock()
        self._events: list[SearchEvent] = []
        self._sequence = 0
        self._closed = False

    def search(self, query: SearchQuery | None = None) -> SearchResult:
        """Run one deterministic local query against caller-supplied entries."""
        with self._lock:
            self._ensure_open()
            result = self._storage.search(query if query is not None else SearchQuery())
            self._record(SearchEventType.SEARCHED)
            return result

    def suggest(self, keyword: str, limit: int = 10) -> tuple[str, ...]:
        """Return deterministic local suggestions without a search engine."""
        with self._lock:
            self._ensure_open()
            suggestions = self._storage.suggest(keyword, limit)
            self._record(SearchEventType.SUGGESTED)
            return suggestions

    def statistics(self) -> SearchStatistics:
        """Return fresh local query statistics, including after close."""
        with self._lock:
            return self._storage.statistics()

    def snapshot(self) -> SearchSnapshot:
        """Return the final immutable local result snapshot, including after close."""
        with self._lock:
            return SearchSnapshot(
                results=self._storage.snapshot(),
                events=tuple(self._events),
                statistics=self._storage.statistics(),
                closed=self._closed,
            )

    def clear(self) -> tuple[object, ...]:
        """Clear only caller-supplied reference entries and record the action."""
        with self._lock:
            self._ensure_open()
            cleared = self._storage.clear()
            if cleared:
                self._record(SearchEventType.CLEARED)
            return cleared

    def close(self) -> None:
        """Close idempotently while retaining final snapshots and statistics."""
        with self._lock:
            if self._closed:
                return
            self._record(SearchEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _record(self, event_type: SearchEventType) -> None:
        self._sequence += 1
        self._events.append(SearchEvent(self._sequence, event_type))

    def _ensure_open(self) -> None:
        if self._closed:
            raise SearchClosedError("Reference Search service is closed.")
