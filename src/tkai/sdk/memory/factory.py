"""Explicit, thread-safe factory for reference and future Memory SDK builders."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from .base import Memory
from .configuration import MemoryConfiguration
from .errors import MemoryNotFoundError


class MemoryFactory:
    """Create only caller-registered memory implementations."""

    def __init__(self) -> None:
        self._builders: dict[str, Callable[[MemoryConfiguration], Memory]] = {}
        self._lock = RLock()

    def register(
        self, name: str, builder: Callable[[MemoryConfiguration], Memory]
    ) -> None:
        """Register one uniquely named explicit memory builder."""
        with self._lock:
            if name in self._builders:
                raise ValueError(f"Memory builder already registered: {name}")
            self._builders[name] = builder

    def create(
        self, name: str, configuration: MemoryConfiguration | None = None
    ) -> Memory:
        """Create a memory through the selected explicit local builder."""
        with self._lock:
            try:
                builder = self._builders[name]
            except KeyError as error:
                raise MemoryNotFoundError(
                    f"Memory builder not registered: {name}"
                ) from error
        return builder(configuration or MemoryConfiguration())
