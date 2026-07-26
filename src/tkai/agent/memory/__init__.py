"""Scoped short memory and an explicit long-memory interface."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from threading import RLock
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class MemoryNamespace:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Memory namespace is required.")


@dataclass(frozen=True, slots=True)
class RetentionPolicy:
    max_items: int = 100

    def __post_init__(self) -> None:
        if self.max_items < 1:
            raise ValueError("Memory retention must allow at least one item.")


class LongMemory(Protocol):
    def get(self, namespace: MemoryNamespace, key: str) -> Any | None: ...
    def put(self, namespace: MemoryNamespace, key: str, value: Any) -> None: ...
    def delete(self, namespace: MemoryNamespace, key: str) -> bool: ...


class ShortMemory:
    """Thread-safe bounded in-process memory, owned by one runtime."""

    def __init__(self, retention: RetentionPolicy | None = None) -> None:
        self.retention = retention or RetentionPolicy()
        self._items: dict[str, dict[str, Any]] = {}
        self._order: dict[str, list[str]] = {}
        self._lock = RLock()

    def put(self, namespace: MemoryNamespace, key: str, value: Any) -> None:
        if not key:
            raise ValueError("Memory key is required.")
        with self._lock:
            items = self._items.setdefault(namespace.value, {})
            order = self._order.setdefault(namespace.value, [])
            if key in order:
                order.remove(key)
            items[key] = value
            order.append(key)
            while len(order) > self.retention.max_items:
                items.pop(order.pop(0), None)

    def get(self, namespace: MemoryNamespace, key: str) -> Any | None:
        with self._lock:
            return self._items.get(namespace.value, {}).get(key)

    def delete(self, namespace: MemoryNamespace, key: str) -> bool:
        with self._lock:
            items = self._items.get(namespace.value, {})
            found = key in items
            items.pop(key, None)
            if key in self._order.get(namespace.value, []):
                self._order[namespace.value].remove(key)
            return found

    def snapshot(self, namespace: MemoryNamespace) -> Mapping[str, Any]:
        with self._lock:
            return dict(self._items.get(namespace.value, {}))
