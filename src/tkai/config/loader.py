"""
TKAI Configuration Loader

Issue-002.2
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Load YAML configuration files."""

    @staticmethod
    def load(path: Path) -> dict[str, Any]:
        """
        Load a YAML configuration file.

        Returns an empty dictionary if the file does not exist.
        """

        if not path.exists():
            return {}

        if not path.is_file():
            raise ValueError(f"{path} is not a file")

        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if data is None:
            return {}

        if not isinstance(data, dict):
            raise ValueError("Configuration root must be a dictionary")

        return data

    @staticmethod
    def load_user() -> dict[str, Any]:
        """
        Load user configuration.

        Path:
            ~/.tkai/config.yaml
        """

        path = Path.home() / ".tkai" / "config.yaml"
        return ConfigLoader.load(path)

    @staticmethod
    def load_project(root: Path | None = None) -> dict[str, Any]:
        """
        Load project configuration.

        Path:
            ./.tkai/config.yaml
        """

        if root is None:
            root = Path.cwd()

        path = root / ".tkai" / "config.yaml"
        return ConfigLoader.load(path)