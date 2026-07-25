"""Reference-only Marketplace Server Search Foundation exports."""

from .errors import SearchClosedError, SearchError, SearchValidationError
from .models import (
    SearchEntry,
    SearchEvent,
    SearchEventType,
    SearchFilter,
    SearchPage,
    SearchQuery,
    SearchResult,
    SearchSnapshot,
    SearchSort,
    SearchStatistics,
    SearchTarget,
)
from .service import ReferenceSearchService
from .storage import ReferenceSearchStorage, SearchStorage

__all__ = (
    "ReferenceSearchService",
    "ReferenceSearchStorage",
    "SearchClosedError",
    "SearchEntry",
    "SearchError",
    "SearchEvent",
    "SearchEventType",
    "SearchFilter",
    "SearchPage",
    "SearchQuery",
    "SearchResult",
    "SearchSnapshot",
    "SearchSort",
    "SearchStatistics",
    "SearchStorage",
    "SearchTarget",
    "SearchValidationError",
)
