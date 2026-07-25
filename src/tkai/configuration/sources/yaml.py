"""YAML file configuration source."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import yaml

from ..loader import ConfigurationLoader


class YAMLConfigurationLoader(ConfigurationLoader):
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> Mapping[str, Any]:
        return (
            yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
            if self.path.exists()
            else {}
        )

    def identifier(self) -> str:
        return "workspace" if self.path.name.startswith(".") else "user"
