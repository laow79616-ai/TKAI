"""JSON file configuration source."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..loader import ConfigurationLoader


class JSONConfigurationLoader(ConfigurationLoader):
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> Mapping[str, Any]:
        return (
            json.loads(self.path.read_text(encoding="utf-8"))
            if self.path.exists()
            else {}
        )

    def identifier(self) -> str:
        return "workspace" if self.path.name.startswith(".") else "user"
