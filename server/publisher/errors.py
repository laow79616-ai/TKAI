"""Stable errors for the local-only Marketplace Server Publisher Foundation."""


class PublisherError(Exception):
    """Base Publisher Foundation error without transport or storage details."""


class PublisherValidationError(PublisherError):
    """Raised when a caller-provided Publisher descriptor is invalid."""


class PublisherConflictError(PublisherError):
    """Raised for duplicate Publisher identifiers or capabilities."""


class PublisherNotFoundError(PublisherError):
    """Raised when an explicit Publisher record is absent."""


class PublisherStateError(PublisherError):
    """Raised when a descriptive Publisher lifecycle change is not allowed."""


class PublisherClosedError(PublisherError):
    """Raised after a closed Publisher service accepts a write operation."""
