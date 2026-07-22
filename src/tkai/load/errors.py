"""Typed errors for the isolated in-memory provider load subsystem."""


class LoadError(RuntimeError):
    """Base error for load registry and passive collection operations."""


class ProviderLoadNotFoundError(LoadError):
    """Raised when a provider has no registered load snapshot."""
