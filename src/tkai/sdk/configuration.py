"""Small immutable configuration SDK with explicit source precedence."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Configuration:
    """Read-only merged values produced by SDK configuration sources."""

    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", MappingProxyType(dict(self.values)))

    def get(self, key: str, default: object | None = None) -> object | None:
        """Read one top-level configuration value without mutation."""
        return self.values.get(key, default)


class ConfigurationSource(Protocol):
    """Protocol for YAML, environment, Python, or future SDK config sources."""

    def load(self) -> Mapping[str, object]: ...


@dataclass(frozen=True, slots=True)
class MappingConfigurationSource:
    """Explicit in-memory source suitable for YAML adapters and tests."""

    values: Mapping[str, object]

    def load(self) -> Mapping[str, object]:
        """Return a defensive shallow copy of configured values."""
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class EnvironmentConfigurationSource:
    """Read selected environment keys, optionally stripping a common prefix."""

    prefix: str = "TKAI_"

    def load(self) -> Mapping[str, object]:
        """Return matching values without exposing the entire process environment."""
        return {
            key.removeprefix(self.prefix).lower(): value
            for key, value in os.environ.items()
            if key.startswith(self.prefix)
        }


@dataclass(frozen=True, slots=True)
class PythonConfigurationSource:
    """Use an application-provided mapping as the Python configuration source."""

    values: Mapping[str, object]

    def load(self) -> Mapping[str, object]:
        """Return a defensive shallow copy of Python-provided settings."""
        return dict(self.values)


class ConfigurationLoader:
    """Merge sources in declaration order; later values take precedence."""

    def __init__(self, sources: tuple[ConfigurationSource, ...] = ()) -> None:
        self.sources = sources

    def load(self) -> Configuration:
        """Merge source results without mutating source-owned mappings."""
        merged: dict[str, object] = {}
        for source in self.sources:
            merged.update(source.load())
        return Configuration(merged)
