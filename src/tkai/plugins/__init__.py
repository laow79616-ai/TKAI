"""Public plugin framework APIs."""

from .discovery import PluginDiscovery
from .hooks import Hook
from .loader import PluginLoader
from .manager import Plugin, PluginManager
from .manifest import PluginManifest
from .models import PluginMetadata
from .registry import PluginRegistry

__all__ = (
    "Plugin",
    "PluginDiscovery",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginMetadata",
    "Hook",
    "PluginRegistry",
)
