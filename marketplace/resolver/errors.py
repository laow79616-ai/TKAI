"""Stable errors for the offline Marketplace Dependency Resolver Foundation."""


class ResolverError(Exception):
    """Base Resolver Foundation error."""


class ResolverValidationError(ResolverError):
    """Raised for structurally invalid resolver models or requests."""


class ResolverClosedError(ResolverError):
    """Raised for operations attempted after a resolver service is closed."""


class ResolverGraphError(ResolverError):
    """Raised for invalid direct DependencyGraphBuilder operations."""


class ResolverInputError(ResolverError):
    """Raised when a caller supplies an unsupported explicit source input."""
