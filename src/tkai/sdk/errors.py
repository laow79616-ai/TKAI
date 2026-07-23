"""Typed errors for the additive TKAI 2.0 SDK surface."""


class SDKError(RuntimeError):
    """Base error for SDK contracts without changing V1.x errors."""


class SDKConfigurationError(SDKError):
    """Raised when an SDK facade has no configured runtime implementation."""


class ExtensionRegistrationError(SDKError):
    """Raised when an extension name conflicts with an existing registration."""
