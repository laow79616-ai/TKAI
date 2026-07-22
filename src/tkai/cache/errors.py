"""Typed errors for the pluggable local cache framework."""


class CacheError(RuntimeError):
    """Base cache framework error."""


class CacheBackendNotFoundError(CacheError):
    """Raised when a named cache backend is not registered."""
