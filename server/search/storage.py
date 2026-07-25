"""Search storage protocol and pure-memory reference implementation."""

from __future__ import annotations

from threading import RLock
from typing import Protocol

from .errors import SearchClosedError
from .models import (
    SearchEntry,
    SearchFilter,
    SearchPage,
    SearchQuery,
    SearchResult,
    SearchSort,
    SearchStatistics,
)


class SearchStorage(Protocol):
    """Explicit local Search storage contract without an index or network."""

    def search(self, query: SearchQuery) -> SearchResult: ...

    def suggest(self, keyword: str, limit: int = 10) -> tuple[str, ...]: ...

    def snapshot(self) -> tuple[SearchEntry, ...]: ...

    def statistics(self) -> SearchStatistics: ...

    def clear(self) -> tuple[SearchEntry, ...]: ...

    def close(self) -> None: ...


class ReferenceSearchStorage:
    """Thread-safe pure-memory Search storage for explicitly supplied entries."""

    def __init__(self, entries: tuple[SearchEntry, ...] = ()) -> None:
        self._lock = RLock()
        self._entries: dict[str, SearchEntry] = {
            entry.identifier: entry for entry in entries
        }
        self._last_results: tuple[SearchEntry, ...] = ()
        self._queries = 0
        self._suggestions = 0
        self._results = 0
        self._closed = False

    def search(self, query: SearchQuery) -> SearchResult:
        with self._lock:
            self._ensure_open()
            matches = [
                entry
                for entry in self._entries_in_order()
                if self._matches(entry, query.search_filter, query.keyword)
            ]
            matches.sort(
                key=lambda entry: self._sort_key(entry, query.sort, query.keyword),
                reverse=query.descending,
            )
            paged = self._page(matches, query.page)
            self._last_results = tuple(paged)
            self._queries += 1
            self._results += len(paged)
            return SearchResult(tuple(paged), len(matches), query.page)

    def suggest(self, keyword: str, limit: int = 10) -> tuple[str, ...]:
        with self._lock:
            self._ensure_open()
            if limit <= 0:
                return ()
            normalized = keyword.casefold()
            candidates = {
                value
                for entry in self._entries.values()
                for value in (entry.name, entry.identifier, *entry.keywords)
                if normalized in value.casefold()
            }
            self._suggestions += 1
            return tuple(sorted(candidates)[:limit])

    def snapshot(self) -> tuple[SearchEntry, ...]:
        """Return the most recent immutable result set, including after close."""
        with self._lock:
            return self._last_results

    def statistics(self) -> SearchStatistics:
        """Return current counts even after close."""
        with self._lock:
            return SearchStatistics(
                queries=self._queries,
                suggestions=self._suggestions,
                targets=len({entry.target for entry in self._entries.values()}),
                results=self._results,
                closed=self._closed,
            )

    def clear(self) -> tuple[SearchEntry, ...]:
        with self._lock:
            self._ensure_open()
            entries = self._entries_in_order()
            self._entries.clear()
            self._last_results = ()
            return entries

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _entries_in_order(self) -> tuple[SearchEntry, ...]:
        return tuple(self._entries[identifier] for identifier in sorted(self._entries))

    def _ensure_open(self) -> None:
        if self._closed:
            raise SearchClosedError("Reference Search storage is closed.")

    @staticmethod
    def _page(entries: list[SearchEntry], page: SearchPage) -> list[SearchEntry]:
        return entries[page.offset : page.offset + page.limit]

    @staticmethod
    def _matches(entry: SearchEntry, search_filter: SearchFilter, keyword: str) -> bool:
        if (
            search_filter.target is not None
            and entry.target is not search_filter.target
        ):
            return False
        if (
            search_filter.publisher is not None
            and entry.publisher != search_filter.publisher
        ):
            return False
        if search_filter.package is not None and entry.package != search_filter.package:
            return False
        if (
            search_filter.category is not None
            and entry.category != search_filter.category
        ):
            return False
        if search_filter.tag is not None and search_filter.tag not in entry.tags:
            return False
        if search_filter.version is not None and entry.version != search_filter.version:
            return False
        if search_filter.status is not None and entry.status != search_filter.status:
            return False
        normalized = keyword.casefold()
        if not normalized:
            return True
        searchable = " ".join(
            (
                entry.identifier,
                entry.name,
                "" if entry.publisher is None else entry.publisher,
                "" if entry.package is None else entry.package,
                "" if entry.category is None else entry.category,
                "" if entry.version is None else entry.version,
                "" if entry.status is None else entry.status,
                *entry.tags,
                *entry.keywords,
            )
        ).casefold()
        return normalized in searchable

    @staticmethod
    def _sort_key(
        entry: SearchEntry, sort: SearchSort, keyword: str
    ) -> tuple[int, str, str]:
        normalized = keyword.casefold()
        relevance = 0
        if normalized:
            relevance = int(normalized in entry.name.casefold()) * 2
            relevance += int(normalized in entry.identifier.casefold())
            relevance += int(
                any(normalized in value.casefold() for value in entry.keywords)
            )
        values = {
            SearchSort.RELEVANCE: "",
            SearchSort.NAME: entry.name,
            SearchSort.IDENTIFIER: entry.identifier,
        }
        return (-relevance, values[sort], entry.identifier)
