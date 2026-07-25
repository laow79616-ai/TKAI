"""Stable errors for offline, reference-only publication contracts."""


class PublicationError(Exception):
    """Base error for publication model, policy, and service operations."""


class PublicationValidationError(PublicationError):
    """Raised when a request or state cannot pass local structural validation."""


class PublicationConflictError(PublicationError):
    """Raised for a duplicate local publication coordinate."""


class PublicationNotFoundError(PublicationError):
    """Raised when an explicit publication id is absent from a local service."""


class PublicationStateError(PublicationError):
    """Raised when a requested local lifecycle transition is not permitted."""


class PublicationClosedError(PublicationError):
    """Raised when an operation is attempted after service close."""
