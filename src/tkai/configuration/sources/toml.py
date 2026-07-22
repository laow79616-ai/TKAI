"""TOML file configuration source."""

from __future__ import annotations

import importlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

from ..loader import ConfigurationLoader


class TOMLConfigurationLoader(ConfigurationLoader):
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> Mapping[str, Any]:
        if not self.path.exists():
            return {}
        toml = importlib.import_module("tomllib")
        contents = toml.loads(self.path.read_text(encoding="utf-8"))
        return cast(Mapping[str, Any], contents)

    def identifier(self) -> str:
        return "workspace" if self.path.name.startswith(".") else "user"
