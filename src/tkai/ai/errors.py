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


class CapabilityNotSupportedError(ProviderError):
    """An explicit provider or model does not meet a required capability set."""


class NoCapableProviderError(ProviderError):
    """No registered provider satisfies the requested capability set."""


class FallbackExhaustedError(ProviderError):
    """Every eligible provider candidate failed within the configured budget."""

    def __init__(
        self,
        attempted_providers: tuple[str, ...],
        failure_summaries: tuple[str, ...],
    ) -> None:
        """Build a safe summary without including raw provider error content."""
        self.attempted_providers = attempted_providers
        self.failure_summaries = failure_summaries
        attempts = ", ".join(attempted_providers) or "none"
        details = "; ".join(failure_summaries) or "no eligible candidates"
        super().__init__(
            f"Provider fallback exhausted. Attempted: {attempts}. {details}"
        )
