"""Reusable helpers for safely working with nested configuration mappings."""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping
from copy import deepcopy
from typing import Any


def deep_merge(
    target: MutableMapping[str, Any], source: Mapping[str, Any]
) -> None:
    """Merge ``source`` into ``target`` without sharing mutable values."""
    for key, value in source.items():
        current = target.get(key)
        if isinstance(current, dict) and isinstance(value, Mapping):
            deep_merge(current, value)
        else:
            target[key] = deepcopy(value)


def get_dotted(
    values: Mapping[str, Any], key: str, default: Any = None
) -> Any:
    """Return a dotted-path value, or ``default`` when the path is absent."""
    current: Any = values
    for part in key.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return default
        current = current[part]
    return current


def set_dotted(
    values: MutableMapping[str, Any], key: str, value: Any
) -> None:
    """Set a dotted-path value, creating intermediate mappings as needed."""
    parts = key.split(".")
    current: MutableMapping[str, Any] = values
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = value
