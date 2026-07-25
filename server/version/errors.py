"""Stable errors for the local-only Marketplace Server Version Foundation."""


class VersionError(Exception):
    """Base Version Foundation error without transport or storage detail."""


class VersionConflictError(VersionError):
    """Raised for duplicate local Version identifiers."""


class VersionValidationError(VersionError):
    """Raised when an explicit Version descriptor is structurally invalid."""


class VersionNotFoundError(VersionError):
    """Raised when an explicit local Version record is absent."""


class VersionClosedError(VersionError):
    """Raised after a closed Version service receives a write operation."""


class VersionStateError(VersionError):
    """Raised when a descriptive Version lifecycle transition is invalid."""
