"""Errors for the local-only Marketplace Server Registry Foundation."""


class RegistryError(Exception):
    """Base Registry Foundation error with no transport or storage detail."""


class RegistryConflictError(RegistryError):
    """Raised for duplicate reference registry identifiers or coordinates."""


class RegistryValidationError(RegistryError):
    """Raised when a caller-provided descriptor is structurally invalid."""


class RegistryNotFoundError(RegistryError):
    """Raised when an explicit reference registry entry is absent."""


class RegistryClosedError(RegistryError):
    """Raised after a closed reference registry accepts no further operations."""


class RegistryStateError(RegistryError):
    """Raised when a descriptive registry state transition is invalid."""
