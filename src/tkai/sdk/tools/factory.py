"""Explicit, thread-safe Tool SDK factory for caller-registered builders."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from .errors import ToolNotFoundError
from .tool import Tool


class ToolFactory:
    """Construct only tools registered explicitly by the application."""

    def __init__(self) -> None:
        self._builders: dict[str, Callable[[], Tool]] = {}
        self._lock = RLock()

    def register(self, name: str, builder: Callable[[], Tool]) -> None:
        """Register one unique local tool builder."""
        with self._lock:
            if name in self._builders:
                raise ValueError(f"Tool builder already registered: {name}")
            self._builders[name] = builder

    def create(self, name: str) -> Tool:
        """Create one caller-selected tool from its registered builder."""
        with self._lock:
            try:
                builder = self._builders[name]
            except KeyError as error:
                raise ToolNotFoundError(
                    f"Tool builder not registered: {name}"
                ) from error
        return builder()
