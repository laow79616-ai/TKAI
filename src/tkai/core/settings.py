"""
TKAI Core Settings

Unified runtime settings.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any

from .mappings import deep_merge, get_dotted, set_dotted


class Settings:
    """Application settings manager."""

    def __init__(self, defaults: dict[str, Any] | None = None) -> None:
        self._defaults = deepcopy(defaults or {})
        self._values = deepcopy(self._defaults)

    @property
    def data(self) -> dict[str, Any]:
        """Return a copy of current settings."""
        return deepcopy(self._values)

    def reset(self) -> None:
        """Reset to defaults."""
        self._values = deepcopy(self._defaults)

    def get(self, key: str, default: Any = None) -> Any:
        """Get value by dotted key."""
        return get_dotted(self._values, key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value by dotted key."""
        set_dotted(self._values, key, value)

    def merge(self, values: dict[str, Any]) -> None:
        """Deep merge settings."""

        deep_merge(self._values, values)

    def load_environment(self, prefix: str = "TKAI_") -> None:
        """Load environment variables."""
        for key, value in os.environ.items():
            if key.startswith(prefix):
                self.set(
                    key[len(prefix) :].lower().replace("_", "."),
                    value,
                )
