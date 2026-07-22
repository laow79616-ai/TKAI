"""Persistent configuration facade."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .models import Configuration
from .resolver import ConfigurationResolver, deep_merge


class ConfigurationManager:
    """Load, reload, merge, and inspect immutable resolved configuration."""

    def __init__(self, resolver: ConfigurationResolver) -> None:
        self.resolver = resolver
        self._configuration = Configuration()

    def load(self) -> Configuration:
        self._configuration = self.resolver.resolve()
        return self._configuration

    def reload(self) -> Configuration:
        self.resolver.reload()
        return self.load()

    def get(self, key: str, default: Any = None) -> Any:
        return self._configuration.get(key, default)

    def has(self, key: str) -> bool:
        return self._configuration.has(key)

    def list(self) -> Configuration:
        return self._configuration

    def merge(self, override: Mapping[str, Any]) -> Configuration:
        return Configuration(
            deep_merge(self._configuration.data, override),
            self._configuration.source,
            self._configuration.overrides + ("memory",),
        )
