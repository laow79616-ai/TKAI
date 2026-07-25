"""Typed errors for the additive TKAI 2.0 SDK surface."""


class SDKError(RuntimeError):
    """Base error for SDK contracts without changing V1.x errors."""


class SDKConfigurationError(SDKError):
    """Raised when an SDK facade has no configured runtime implementation."""


class AdapterError(SDKError):
    """Raised when an explicitly supplied runtime dependency cannot be adapted."""


class ProviderExecutionError(SDKError):
    """Raised with the original provider exception preserved as its cause."""


class SDKMemoryError(SDKError):
    """Raised when a memory adapter receives invalid local storage input."""


class InvalidRequestError(SDKError):
    """Raised before an invalid SDK request reaches an injected provider."""


class ExtensionRegistrationError(SDKError):
    """Raised when an extension name conflicts with an existing registration."""
