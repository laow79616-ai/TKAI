"""Immutable, deterministic Marketplace Server Search domain models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..api import Filtering, Pagination


def _copy(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


class SearchTarget(str, Enum):
    """Explicit local targets for unified reference searches."""

    REGISTRY = "registry"
    PUBLISHER = "publisher"
    PACKAGE = "package"
    VERSION = "version"


class SearchSort(str, Enum):
    """Stable local Search sorting keys."""

    RELEVANCE = "relevance"
    NAME = "name"
    VERSION = "version"
    IDENTIFIER = "identifier"


class SearchEventType(str, Enum):
    """Deterministic local Search events with no EventBus dependency."""

    SEARCHED = "searched"
    SUGGESTED = "suggested"
    CLEARED = "cleared"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class SearchPage:
    """Explicit deterministic page request for local Search results."""

    offset: int = 0
    limit: int = 50

    def __post_init__(self) -> None:
        if self.offset < 0 or self.limit <= 0:
            raise ValueError(
                "Search page offset must be non-negative and limit positive."
            )


@dataclass(frozen=True, slots=True)
class SearchFilter:
    """Explicit filters applied to caller-supplied local Search entries."""

    target: SearchTarget | None = None
    publisher: str | None = None
    package: str | None = None
    category: str | None = None
    tag: str | None = None
    version: str | None = None
    status: str | None = None
    filtering: Filtering = field(default_factory=Filtering)


@dataclass(frozen=True, slots=True, init=False)
class SearchQuery:
    """Unified local query; empty keywords select all matching local entries."""

    keyword: str
    search_filter: SearchFilter
    sort: SearchSort
    descending: bool
    page: SearchPage
    pagination: Pagination

    def __init__(
        self,
        text: str = "",
        search_filter: SearchFilter | None = None,
        sort: SearchSort = SearchSort.RELEVANCE,
        pagination: Pagination | None = None,
        *,
        keyword: str | None = None,
        descending: bool = False,
        page: SearchPage | None = None,
    ) -> None:
        """Accept the Sprint-1 ``text`` form and the Sprint-6 keyword form."""
        if keyword is not None and text and keyword != text:
            raise ValueError("Search text and keyword must match when both are set.")
        resolved_pagination = pagination if pagination is not None else Pagination()
        resolved_page = (
            page
            if page is not None
            else SearchPage(resolved_pagination.offset, resolved_pagination.limit)
        )
        object.__setattr__(self, "keyword", text if keyword is None else keyword)
        object.__setattr__(
            self,
            "search_filter",
            search_filter if search_filter is not None else SearchFilter(),
        )
        object.__setattr__(self, "sort", sort)
        object.__setattr__(self, "descending", descending)
        object.__setattr__(self, "page", resolved_page)
        object.__setattr__(self, "pagination", resolved_pagination)

    @property
    def text(self) -> str:
        """Expose the stable Sprint-1 text alias for the unified keyword."""
        return self.keyword


@dataclass(frozen=True, slots=True)
class SearchEntry:
    """Caller-supplied searchable description with no implicit cross-domain lookup."""

    identifier: str
    target: SearchTarget
    name: str
    publisher: str | None = None
    package: str | None = None
    category: str | None = None
    tags: frozenset[str] = field(default_factory=frozenset)
    version: str | None = None
    status: str | None = None
    keywords: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.identifier or not self.name:
            raise ValueError("Search entry identifier and name are required.")
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "keywords", tuple(self.keywords))
        object.__setattr__(self, "metadata", _copy(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready local Search entry."""
        return {
            "identifier": self.identifier,
            "target": self.target.value,
            "name": self.name,
            "publisher": self.publisher,
            "package": self.package,
            "category": self.category,
            "tags": sorted(self.tags),
            "version": self.version,
            "status": self.status,
            "keywords": list(self.keywords),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    """Immutable page of deterministic local Search entries."""

    entries: tuple[object, ...] = ()
    total: int = 0
    page: SearchPage = field(default_factory=SearchPage)

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Search result."""
        return {
            "entries": [
                entry.to_dict() if isinstance(entry, SearchEntry) else entry
                for entry in self.entries
            ],
            "total": self.total,
            "offset": self.page.offset,
            "limit": self.page.limit,
        }


@dataclass(frozen=True, slots=True)
class SearchEvent:
    """Sequence-ordered local Search event without timestamps."""

    sequence: int
    event_type: SearchEventType

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Search event."""
        return {"sequence": self.sequence, "event_type": self.event_type.value}


@dataclass(frozen=True, slots=True)
class SearchStatistics:
    """Fresh Search operation and current-target statistics."""

    queries: int = 0
    suggestions: int = 0
    targets: int = 0
    results: int = 0
    closed: bool = False

    def to_dict(self) -> dict[str, object]:
        """Return JSON-ready count-only Search statistics."""
        return {
            "queries": self.queries,
            "suggestions": self.suggestions,
            "targets": self.targets,
            "results": self.results,
            "closed": self.closed,
        }


@dataclass(frozen=True, slots=True)
class SearchSnapshot:
    """Stable immutable final results, events, statistics, and close state."""

    query: SearchQuery | None = None
    result: SearchResult = field(default_factory=SearchResult)
    results: tuple[SearchEntry, ...] = ()
    events: tuple[SearchEvent, ...] = ()
    statistics: SearchStatistics = field(default_factory=SearchStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        if not self.results and all(
            isinstance(entry, SearchEntry) for entry in self.result.entries
        ):
            object.__setattr__(self, "results", tuple(self.result.entries))
        object.__setattr__(self, "results", tuple(self.results))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready immutable Search snapshot."""
        return {
            "query": None if self.query is None else self.query.text,
            "result": self.result.to_dict(),
            "results": [result.to_dict() for result in self.results],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }
