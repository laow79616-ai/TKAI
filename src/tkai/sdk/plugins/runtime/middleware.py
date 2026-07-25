"""Reserved local middleware contract for future explicit Plugin Runtime adapters."""

from __future__ import annotations

from typing import Protocol

from .manifest import PluginManifest


class PluginMiddleware(Protocol):
    """Observe a plugin execution boundary without changing plugin ownership."""

    def before_execute(self, manifest: PluginManifest) -> None: ...

    def after_execute(self, manifest: PluginManifest) -> None: ...

    def on_error(self, error: Exception) -> None: ...
