"""Reference-only Plugin Runtime contracts and explicit local implementations."""

from .dependency import PluginDependency, resolve_dependencies
from .descriptor import PluginDescriptor
from .errors import (
    PluginDependencyError,
    PluginLifecycleError,
    PluginNotFoundError,
    PluginRuntimeError,
)
from .hooks import PluginHook, TelemetryPluginHook
from .lifecycle import PluginLifecycle
from .loader import PluginLoader
from .manifest import PluginManifest
from .middleware import PluginMiddleware
from .registry import PluginRegistry
from .runtime import (
    EchoPlugin,
    MemoryPlugin,
    Plugin,
    PluginContext,
    PluginRuntime,
    WorkflowPlugin,
)

__all__ = (
    "EchoPlugin",
    "MemoryPlugin",
    "Plugin",
    "PluginContext",
    "PluginDependency",
    "PluginDependencyError",
    "PluginDescriptor",
    "PluginHook",
    "PluginLifecycle",
    "PluginLifecycleError",
    "PluginLoader",
    "PluginManifest",
    "PluginMiddleware",
    "PluginNotFoundError",
    "PluginRegistry",
    "PluginRuntime",
    "PluginRuntimeError",
    "TelemetryPluginHook",
    "WorkflowPlugin",
    "resolve_dependencies",
)
