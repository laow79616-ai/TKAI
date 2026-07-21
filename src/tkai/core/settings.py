"""
TKAI Core Settings

Unified runtime settings.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any


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
        current: Any = self._values

        for part in key.split("."):
            if not isinstance(current, dict):
                return default

            if part not in current:
                return default

            current = current[part]

        return current

    def set(self, key: str, value: Any) -> None:
        """Set value by dotted key."""
        current = self._values
        parts = key.split(".")

        for part in parts[:-1]:
            current = current.setdefault(part, {})

        current[parts[-1]] = value

    def merge(self, values: dict[str, Any]) -> None:
        """Deep merge settings."""

        def merge_dict(dst: dict[str, Any], src: dict[str, Any]) -> None:
            for key, value in src.items():
                if (
                    key in dst
                    and isinstance(dst[key], dict)
                    and isinstance(value, dict)
                ):
                    merge_dict(dst[key], value)
                else:
                    dst[key] = deepcopy(value)

        merge_dict(self._values, values)

    def load_environment(self, prefix: str = "TKAI_") -> None:
        """Load environment variables."""
        for key, value in os.environ.items():
            if key.startswith(prefix):
                self.set(
                    key[len(prefix):].lower().replace("_", "."),
                    value,
                )