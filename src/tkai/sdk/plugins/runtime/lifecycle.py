"""Explicit lifecycle states for local Plugin Runtime objects."""

from enum import Enum


class PluginLifecycle(str, Enum):
    """Small state model; no plugin action occurs automatically."""

    CREATED = "created"
    LOADED = "loaded"
    INITIALIZED = "initialized"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNLOADED = "unloaded"
    SHUTDOWN = "shutdown"
