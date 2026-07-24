"""Stable Tenant Boundary errors with no transport, storage, or secret detail."""

from ..errors import EnterpriseArchitectureError


class TenantError(EnterpriseArchitectureError):
    """Base error for Tenant Boundary operations."""


class TenantNotFoundError(TenantError):
    """Raised when an explicitly requested tenant is unavailable."""


class TenantConflictError(TenantError):
    """Raised when a duplicate tenant identifier or slug is registered."""


class TenantValidationError(TenantError):
    """Raised when a tenant descriptor or context is invalid."""


class TenantResolutionError(TenantError):
    """Raised when an injected resolver cannot resolve an explicit request."""


class TenantIsolationError(TenantError):
    """Raised for invalid isolation descriptors without enforcing isolation."""


class TenantRoutingError(TenantError):
    """Raised when a reference routing policy has no declared route."""


class TenantQuotaError(TenantError):
    """Raised for invalid quota descriptors without enforcing quotas."""


class TenantLifecycleError(TenantError):
    """Raised for an illegal declarative lifecycle transition."""
