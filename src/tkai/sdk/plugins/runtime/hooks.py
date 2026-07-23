"""Optional observation contracts for explicit Plugin Runtime lifecycle actions."""

from __future__ import annotations

from typing import Protocol

from .manifest import PluginManifest


class PluginHook(Protocol):
    """Observe lifecycle and execute boundaries without owning plugin objects."""

    def before_load(self, manifest: PluginManifest) -> None: ...

    def after_load(self, manifest: PluginManifest) -> None: ...

    def before_execute(self, manifest: PluginManifest) -> None: ...

    def after_execute(self, manifest: PluginManifest) -> None: ...

    def on_error(self, manifest: PluginManifest | None, error: Exception) -> None: ...


class TelemetryPluginHook(PluginHook, Protocol):
    """Marker protocol for an explicitly supplied telemetry observer."""
