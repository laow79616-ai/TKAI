"""Stable errors for the local-only Marketplace Server Package Foundation."""


class PackageError(Exception):
    """Base Package Foundation error without transport or storage detail."""


class PackageConflictError(PackageError):
    """Raised for duplicate local Package identifiers."""


class PackageValidationError(PackageError):
    """Raised when an explicit Package descriptor is structurally invalid."""


class PackageNotFoundError(PackageError):
    """Raised when an explicit local Package record is absent."""


class PackageClosedError(PackageError):
    """Raised after a closed Package service receives a write operation."""


class PackageStateError(PackageError):
    """Raised when a descriptive Package lifecycle transition is invalid."""
