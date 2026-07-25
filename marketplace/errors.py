"""Errors for the local, reference-only Marketplace architecture."""


class MarketplaceError(Exception):
    """Base error for Marketplace descriptor and registry operations."""


class PackageConflictError(MarketplaceError):
    """Raised when a package identifier is already present in a registry."""


class PackageNotFoundError(MarketplaceError):
    """Raised when an explicit package identifier cannot be resolved."""


class DependencyResolutionError(MarketplaceError):
    """Raised when a declarative dependency graph is incomplete or cyclic."""
