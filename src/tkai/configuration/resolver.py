"""Priority resolver for local configuration sources."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from copy import deepcopy
from typing import Any

from .loader import ConfigurationLoader
from .models import Configuration


def deep_merge(base: Mapping[str, Any], override: Mapping[str, Any]) -> dict[str, Any]:
    """Return a new recursively merged mapping without mutating either input."""
    result = deepcopy(dict(base))
    for key, value in override.items():
        if isinstance(value, Mapping) and isinstance(result.get(key), Mapping):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


class ConfigurationResolver:
    """Merge sources ordered from lowest to highest precedence."""

    def __init__(self, sources: Iterable[ConfigurationLoader]) -> None:
        self.sources = tuple(sources)

    def resolve(self) -> Configuration:
        data: dict[str, Any] = {}
        identifiers: list[str] = []
        for source in self.sources:
            loaded = source.load()
            if loaded:
                data = deep_merge(data, loaded)
                identifiers.append(source.identifier())
        return Configuration(
            data, identifiers[-1] if identifiers else "default", tuple(identifiers)
        )

    def reload(self) -> None:
        for source in self.sources:
            method = getattr(source, "reload", None)
            if callable(method):
                method()
