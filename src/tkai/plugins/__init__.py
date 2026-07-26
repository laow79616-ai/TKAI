"""Public plugin framework APIs."""

from .catalog import PluginCatalog
from .discovery import PluginDiscovery
from .hooks import Hook
from .installer import PluginInstaller
from .loader import MarketplacePluginLoader, PluginLoader
from .manager import Plugin, PluginManager
from .manifest import PluginManifest
from .marketplace import EnterprisePluginMarketplace, PluginMetrics
from .models import (
    InstalledPlugin,
    PluginDefinition,
    PluginDependency,
    PluginMetadata,
    PluginState,
)
from .permissions import PermissionPolicy, PluginPermission
from .registry import MarketplaceRegistry, PluginRegistry
from .sandbox import ExecutionLimits, PluginSandbox, SandboxPolicy
from .signing import PluginSigner

__all__ = (
    "EnterprisePluginMarketplace",
    "ExecutionLimits",
    "InstalledPlugin",
    "MarketplacePluginLoader",
    "MarketplaceRegistry",
    "PermissionPolicy",
    "Plugin",
    "PluginCatalog",
    "PluginDefinition",
    "PluginDependency",
    "PluginInstaller",
    "PluginDiscovery",
    "PluginLoader",
    "PluginManager",
    "PluginManifest",
    "PluginMetadata",
    "PluginMetrics",
    "PluginPermission",
    "Hook",
    "PluginRegistry",
    "PluginSandbox",
    "PluginSigner",
    "PluginState",
    "SandboxPolicy",
)
