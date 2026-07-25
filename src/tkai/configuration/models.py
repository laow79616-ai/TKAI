"""Immutable persistent configuration model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Configuration:
    """JSON-safe immutable configuration with dotted lookup and safe defaults."""

    data: Mapping[str, Any] = field(default_factory=dict)
    source: str = "default"
    overrides: tuple[str, ...] = ()

    def get(self, key: str, default: Any = None) -> Any:
        value: Any = self.data
        for part in key.split("."):
            if not isinstance(value, Mapping) or part not in value:
                return default
            value = value[part]
        return value

    def has(self, key: str) -> bool:
        return self.get(key, _MISSING) is not _MISSING


_MISSING = object()
