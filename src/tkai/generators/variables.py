"""
TKAI Generator Variables

Variable collection and merge utilities.
"""

from __future__ import annotations

import os
from copy import deepcopy
from typing import Any


class VariableManager:
    """Manage generator variables."""

    def __init__(self) -> None:
        self._variables: dict[str, Any] = {}
        self._defaults: dict[str, Any] = {}

    @property
    def variables(self) -> dict[str, Any]:
        """Return current variables."""
        return deepcopy(self._variables)

    @property
    def defaults(self) -> dict[str, Any]:
        """Return default variables."""
        return deepcopy(self._defaults)

    def clear(self) -> None:
        """Clear all variables."""
        self._variables.clear()

    def reset(self) -> None:
        """Reset to defaults."""
        self._variables = deepcopy(self._defaults)

    def set_default(self, key: str, value: Any) -> None:
        """Set default variable."""
        self._defaults[key] = value

        if key not in self._variables:
            self._variables[key] = deepcopy(value)

    def set(self, key: str, value: Any) -> None:
        """Set variable."""
        self._variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get variable."""
        return self._variables.get(key, default)

    def has(self, key: str) -> bool:
        """Return whether variable exists."""
        return key in self._variables

    def remove(self, key: str) -> Any:
        """Remove variable."""
        return self._variables.pop(key, None)

    def update(self, values: dict[str, Any]) -> None:
        """Update variables."""
        self._variables.update(values)

    def load_environment(
        self,
        prefix: str = "TKAI_",
    ) -> None:
        """
        Load environment variables.

        Example:

            TKAI_AUTHOR=wang
            TKAI_VERSION=1.0.0
        """

        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue

            name = key[len(prefix):].lower()

            self._variables[name] = value

    def merge(
        self,
        *sources: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Merge dictionaries.

        Later dictionaries override earlier ones.
        """

        merged = deepcopy(self._variables)

        for source in sources:
            merged.update(source)

        self._variables = merged

        return deepcopy(self._variables)

    def to_dict(self) -> dict[str, Any]:
        """Serialize variables."""
        return deepcopy(self._variables)

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "VariableManager":
        """Deserialize variables."""

        manager = cls()

        manager.update(data)

        return manager

    def __contains__(self, key: str) -> bool:
        return self.has(key)

    def __len__(self) -> int:
        return len(self._variables)