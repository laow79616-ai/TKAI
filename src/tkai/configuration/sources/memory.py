"""In-memory configuration source."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from ..loader import ConfigurationLoader


class MemoryConfigurationLoader(ConfigurationLoader):
    def __init__(self, data: Mapping[str, Any] | None = None) -> None:
        self.data = deepcopy(dict(data or {}))

    def load(self) -> Mapping[str, Any]:
        return deepcopy(self.data)

    def identifier(self) -> str:
        return "memory"
