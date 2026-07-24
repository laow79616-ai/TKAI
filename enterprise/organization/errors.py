"""Organization Foundation error types without repository or persistence behavior."""

from ..errors import EnterpriseArchitectureError


class OrganizationError(EnterpriseArchitectureError):
    """Base error for explicit Organization Foundation operations."""


class OrganizationNotFoundError(OrganizationError):
    """Raised when a requested reference organization is unavailable."""


class OrganizationConflictError(OrganizationError):
    """Raised when an organization identifier already exists in a registry."""
