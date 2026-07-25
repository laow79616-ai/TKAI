"""Compatibility lifecycle dispatcher for SDK and legacy local plugins."""

from __future__ import annotations

from typing import Any

from tkai.core.context import Context


def initialize_plugin(plugin: Any, context: Context) -> None:
    """Prefer SDK initialize, falling back to the legacy activate signature."""
    initializer = getattr(plugin, "initialize", None)
    if callable(initializer):
        initializer()
        return
    activator = getattr(plugin, "activate", None)
    if callable(activator):
        activator(context)
        return
    raise TypeError("plugin does not define initialize() or activate()")


def shutdown_plugin(plugin: Any, context: Context) -> None:
    """Prefer SDK shutdown, falling back to the legacy deactivate signature."""
    shutdown = getattr(plugin, "shutdown", None)
    if callable(shutdown):
        shutdown()
        return
    deactivator = getattr(plugin, "deactivate", None)
    if callable(deactivator):
        deactivator(context)
        return
    raise TypeError("plugin does not define shutdown() or deactivate()")
