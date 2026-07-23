"""Typed errors for the additive local Plugin Runtime."""

from ...errors import SDKError


class PluginRuntimeError(SDKError):
    """Base error for explicit Plugin Runtime operations."""


class PluginNotFoundError(PluginRuntimeError):
    """Raised when a named plugin has not been registered."""


class PluginDependencyError(PluginRuntimeError):
    """Raised when local plugin dependencies are missing or cyclic."""


class PluginLifecycleError(PluginRuntimeError):
    """Raised when an explicit lifecycle action is invalid for current state."""
