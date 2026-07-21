"""
TKAI Configuration Saver

Issue-002.2
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


class ConfigSaver:
    """Save YAML configuration files."""

    @staticmethod
    def save(
        path: Path,
        config: dict[str, Any],
    ) -> None:
        """
        Save configuration to a YAML file.

        Automatically creates parent directories if they do not exist.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(
                config,
                f,
                allow_unicode=True,
                sort_keys=False,
            )

    @staticmethod
    def save_user(config: dict[str, Any]) -> None:
        """
        Save user configuration.

        Path:
            ~/.tkai/config.yaml
        """

        path = Path.home() / ".tkai" / "config.yaml"
        ConfigSaver.save(path, config)

    @staticmethod
    def save_project(
        config: dict[str, Any],
        root: Path | None = None,
    ) -> None:
        """
        Save project configuration.

        Path:
            ./.tkai/config.yaml
        """

        if root is None:
            root = Path.cwd()

        path = root / ".tkai" / "config.yaml"
        ConfigSaver.save(path, config)