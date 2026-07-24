"""Stable authorization foundation errors without enforcement or secret details."""

from ..errors import EnterpriseArchitectureError


class AuthorizationError(EnterpriseArchitectureError):
    """Base error for explicit Authorization Foundation operations."""


class AuthorizationNotFoundError(AuthorizationError):
    """Raised when a requested reference descriptor is absent."""


class AuthorizationConflictError(AuthorizationError):
    """Raised when a reference descriptor id is already registered."""
