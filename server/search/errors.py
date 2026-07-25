"""Stable errors for the local-only Marketplace Server Search Foundation."""


class SearchError(Exception):
    """Base Search Foundation error without transport or index detail."""


class SearchValidationError(SearchError):
    """Raised when an explicit Search query or entry is structurally invalid."""


class SearchClosedError(SearchError):
    """Raised after a closed Search service accepts a new query or clear operation."""
