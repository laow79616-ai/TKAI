"""Offline Enterprise License Foundation contracts and reference-only service."""

from .models import (
    CapabilitySnapshot,
    Edition,
    Expiration,
    FeatureDescriptor,
    FeatureGroup,
    GracePeriod,
    LicenseCapability,
    LicenseEntitlement,
    LicenseGrant,
    LicenseLimit,
    LicenseUsage,
    RenewalHint,
)
from .service import ReferenceLicenseService
from .validation import (
    LicenseValidationRequest,
    LicenseValidationResult,
    LicenseValidator,
    ReferenceLicenseValidator,
)

__all__ = (
    "CapabilitySnapshot",
    "Edition",
    "Expiration",
    "FeatureDescriptor",
    "FeatureGroup",
    "GracePeriod",
    "LicenseCapability",
    "LicenseEntitlement",
    "LicenseGrant",
    "LicenseLimit",
    "LicenseUsage",
    "LicenseValidationRequest",
    "LicenseValidationResult",
    "LicenseValidator",
    "ReferenceLicenseService",
    "ReferenceLicenseValidator",
    "RenewalHint",
)
