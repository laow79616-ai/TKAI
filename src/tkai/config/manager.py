"""
TKAI Configuration Manager

Issue-002.2
"""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .defaults import DEFAULT_CONFIG
from .loader import ConfigLoader
from .saver import ConfigSaver


class ConfigManager:
    """Manage TKAI configuration."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self.load_default()

    def load_default(self) -> dict[str, Any]:
        """Load default configuration."""
        self._config = deepcopy(DEFAULT_CONFIG)
        return deepcopy(self._config)

    def load_user(self) -> dict[str, Any]:
        """Load and merge user configuration."""
        config = ConfigLoader.load_user()

        if config:
            self.merge(config)

        return deepcopy(self._config)

    def load_project(self, root: Path | None = None) -> dict[str, Any]:
        """Load and merge project configuration."""
        config = ConfigLoader.load_project(root)

        if config:
            self.merge(config)

        return deepcopy(self._config)

    def load_all(self, root: Path | None = None) -> dict[str, Any]:
        """
        Load configuration in order:

        1. Default
        2. User
        3. Project
        """
        self.load_default()
        self.load_user()
        self.load_project(root)

        return deepcopy(self._config)

    def save_user(self) -> None:
        """Save current configuration to the user config file."""
        ConfigSaver.save_user(self._config)

    def save_project(self, root: Path | None = None) -> None:
        """Save current configuration to the project config file."""
        ConfigSaver.save_project(self._config, root)

    def merge(self, config: dict[str, Any]) -> None:
        """Merge configuration into current config."""
        self._merge_dict(self._config, config)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Supports dotted keys.

        Example:
            get("llm.provider")
        """
        value: Any = self._config

        for part in key.split("."):
            if not isinstance(value, dict):
                return default

            if part not in value:
                return default

            value = value[part]

        return value

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.

        Supports dotted keys.

        Example:
            set("llm.provider", "openai")
        """
        parts = key.split(".")
        current = self._config

        for part in parts[:-1]:
            current = current.setdefault(part, {})

        current[parts[-1]] = value

    @property
    def config(self) -> dict[str, Any]:
        """Return a copy of current configuration."""
        return deepcopy(self._config)

    @staticmethod
    def _merge_dict(
        target: dict[str, Any],
        source: dict[str, Any],
    ) -> None:
        """Deep merge dictionaries."""
        for key, value in source.items():
            if (
                key in target
                and isinstance(target[key], dict)
                and isinstance(value, dict)
            ):
                ConfigManager._merge_dict(target[key], value)
            else:
                target[key] = deepcopy(value)