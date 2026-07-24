"""Identity Foundation error types with no authentication protocol behavior."""

from ..errors import EnterpriseArchitectureError


class IdentityError(EnterpriseArchitectureError):
    """Base error for explicit Identity Foundation operations."""


class IdentityNotFoundError(IdentityError):
    """Raised when an explicitly requested reference identity is unavailable."""


class IdentityConflictError(IdentityError):
    """Raised when a registry identifier is already associated with a provider."""
