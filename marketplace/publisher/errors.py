"""Errors for local, reference-only Publisher Foundation operations."""


class PublisherError(Exception):
    """Base error for Publisher descriptor, policy, and registry operations."""


class PublisherConflictError(PublisherError):
    """Raised when a publisher id has already been registered locally."""


class PublisherNotFoundError(PublisherError):
    """Raised when an explicit publisher id is not registered locally."""
