"""Typed errors for the additive, offline Memory SDK framework."""

from ..errors import SDKError


class MemorySDKError(SDKError):
    """Base error for Memory SDK operations."""


class MemoryNotFoundError(MemorySDKError):
    """Raised when an explicit memory name is absent from a registry."""


class MemoryLifecycleError(MemorySDKError):
    """Raised when a closed reference memory receives a new operation."""


class MemoryConfigurationError(MemorySDKError):
    """Raised when immutable memory configuration is invalid."""
