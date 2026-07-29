"""Immutable runtime context values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType


@dataclass(frozen=True)
class RuntimeContext:
    """Context passed to modules during initialization."""

    environment: str = "local"
    values: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def with_value(self, key: str, value: object) -> RuntimeContext:
        values = dict(self.values)
        values[key] = value
        return replace(self, values=MappingProxyType(values))


__all__ = ("RuntimeContext",)
