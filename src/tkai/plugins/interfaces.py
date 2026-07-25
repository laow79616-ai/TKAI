"""SDK plugin interfaces; legacy activate/deactivate plugins remain supported."""

from __future__ import annotations

from typing import Protocol

from .models import PluginMetadata


class Plugin(Protocol):
    """Preferred SDK lifecycle contract for local Python plugins."""

    def initialize(self) -> None:
        """Initialize plugin-local resources without changing global runtime state."""

    def shutdown(self) -> None:
        """Release plugin-local resources."""

    def metadata(self) -> PluginMetadata:
        """Return immutable SDK plugin metadata."""
