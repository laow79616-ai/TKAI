"""Typed provider failures without leaking configuration secrets."""

from tkai.core.exceptions import AIProviderError


class ProviderError(AIProviderError):
    """Base error for provider framework operations."""


class ProviderNotFoundError(ProviderError):
    """Requested provider is not registered."""


class ProviderConfigurationError(ProviderError):
    """Provider configuration is absent or invalid."""


class AuthenticationError(ProviderError):
    """Provider rejected authentication."""


class RateLimitError(ProviderError):
    """Provider rate limit was reached."""


class ModelNotFoundError(ProviderError):
    """Requested model is unavailable."""


class ProviderTimeoutError(ProviderError):
    """Provider request exceeded its timeout."""


class ProviderResponseError(ProviderError):
    """Provider returned an invalid or server-error response."""
