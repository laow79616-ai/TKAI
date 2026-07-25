"""Stable License Foundation errors without activation, signatures, or secrets."""

from ..errors import EnterpriseArchitectureError


class LicenseError(EnterpriseArchitectureError):
    """Base error for explicit License Foundation operations."""


class LicenseNotFoundError(LicenseError):
    """Raised when an explicit reference entitlement is absent."""
