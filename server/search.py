"""Search descriptors only; no index, crawler, or external search engine exists."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .api import Filtering, Pagination


class SearchSort(str, Enum):
    RELEVANCE = "relevance"
    NAME = "name"
    VERSION = "version"


@dataclass(frozen=True, slots=True)
class SearchFilter:
    filtering: Filtering = field(default_factory=Filtering)


@dataclass(frozen=True, slots=True)
class SearchQuery:
    text: str = ""
    search_filter: SearchFilter = field(default_factory=SearchFilter)
    sort: SearchSort = SearchSort.RELEVANCE
    pagination: Pagination = field(default_factory=Pagination)


@dataclass(frozen=True, slots=True)
class SearchResult:
    entries: tuple[object, ...] = ()
    total: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))


@dataclass(frozen=True, slots=True)
class SearchSnapshot:
    query: SearchQuery | None = None
    result: SearchResult = field(default_factory=SearchResult)
