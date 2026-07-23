"""Typed exceptions for optional local multi-region selection."""


class MultiRegionError(RuntimeError):
    """Base multi-region configuration or selection error."""


class RegionNotFoundError(MultiRegionError):
    """Raised when a region is absent from the local registry."""


class NoRegionAvailableError(MultiRegionError):
    """Raised when no supplied region satisfies the explicit policy."""
