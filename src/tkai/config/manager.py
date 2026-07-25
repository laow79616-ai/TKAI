"""
TKAI Configuration Manager

Issue-002.2
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tkai.core.mappings import deep_merge
from tkai.core.settings import Settings

from .defaults import DEFAULT_CONFIG
from .loader import ConfigLoader
from .saver import ConfigSaver


class ConfigManager(Settings):
    """Add YAML persistence and precedence rules to :class:`Settings`.

    ``Settings`` is the sole implementation of nested reads, writes, and
    merges.  This compatibility class keeps the established configuration
    loading and saving API while delegating state management to it.
    """

    def __init__(self) -> None:
        super().__init__(DEFAULT_CONFIG)

    def load_default(self) -> dict[str, Any]:
        """Load default configuration."""
        self.reset()
        return self.data

    def load_user(self) -> dict[str, Any]:
        """Load and merge user configuration."""
        config = ConfigLoader.load_user()

        if config:
            self.merge(config)

        return self.data

    def load_project(self, root: Path | None = None) -> dict[str, Any]:
        """Load and merge project configuration."""
        config = ConfigLoader.load_project(root)

        if config:
            self.merge(config)

        return self.data

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

        return self.data

    def save_user(self) -> None:
        """Save current configuration to the user config file."""
        ConfigSaver.save_user(self.data)

    def save_project(self, root: Path | None = None) -> None:
        """Save current configuration to the project config file."""
        ConfigSaver.save_project(self.data, root)

    @property
    def config(self) -> dict[str, Any]:
        """Return a copy of current configuration."""
        return self.data

    @staticmethod
    def _merge_dict(
        target: dict[str, Any],
        source: dict[str, Any],
    ) -> None:
        """Deep merge dictionaries."""
        deep_merge(target, source)
