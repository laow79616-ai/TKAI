"""Typed failures for optional, explicit adaptive routing."""


class AdaptiveRoutingError(RuntimeError):
    """Base error for invalid adaptive routing configuration or selection."""


class NoAdaptiveProviderError(AdaptiveRoutingError):
    """Raised when every supplied candidate is ineligible."""


class AdaptiveRouterNotFoundError(AdaptiveRoutingError):
    """Raised when a named adaptive router is absent from its registry."""
