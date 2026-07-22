"""Environment override configuration source."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from ..loader import ConfigurationLoader


class EnvironmentConfigurationLoader(ConfigurationLoader):
    def __init__(
        self, environment: Mapping[str, str] | None = None, prefix: str = "TKAI_"
    ) -> None:
        self.environment = environment or os.environ
        self.prefix = prefix

    def load(self) -> Mapping[str, Any]:
        data: dict[str, Any] = {}
        for key, value in self.environment.items():
            if key.startswith(self.prefix):
                parts = key[len(self.prefix) :].lower().split("__")
                target = data
                for part in parts[:-1]:
                    target = target.setdefault(part, {})
                target[parts[-1]] = value
        return data

    def identifier(self) -> str:
        return "environment"
