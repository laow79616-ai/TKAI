"""No-op lifecycle implementation used by bundled integration plugins."""

from __future__ import annotations

from tkai.core.context import Context


class BuiltinPlugin:
    """Provide a stable activation contract for optional integrations."""

    def activate(self, context: Context) -> None:
        """Activate the integration; configuration occurs in its consumer."""

    def deactivate(self, context: Context) -> None:
        """Deactivate the integration without modifying unrelated services."""
