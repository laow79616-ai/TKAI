"""Typed, secret-safe failures for the standalone routing foundation."""


class RoutingError(RuntimeError):
    """Base error for provider routing metadata and registry operations."""


class ProviderMetadataNotFoundError(RoutingError):
    """Raised when a provider has not been registered for routing."""
