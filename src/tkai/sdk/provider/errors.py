"""Provider-SDK errors that keep concrete transport failures as causes."""

from ..errors import SDKError


class ProviderSDKError(SDKError):
    """Base error for provider SDK operations."""


class ProviderNotFoundError(ProviderSDKError):
    """Raised when a requested provider name is absent from a registry."""


class ProviderCapabilityError(ProviderSDKError):
    """Raised when a provider does not declare a required capability."""


class ProviderConfigurationError(ProviderSDKError):
    """Raised when immutable provider settings contain invalid values."""


class ProviderLifecycleError(ProviderSDKError):
    """Raised when a closed provider client is used by a future adapter."""
