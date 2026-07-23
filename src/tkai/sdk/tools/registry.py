"""Thread-safe local registry for explicitly constructed Tool SDK tools."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from .errors import ToolNotFoundError

if TYPE_CHECKING:
    from .tool import Tool


class ToolRegistry:
    """Register local tools without activating external capabilities or transports."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}
        self._lock = RLock()

    def register(self, tool: Tool) -> Tool:
        """Register one unique descriptor name and return its original tool."""
        with self._lock:
            if tool.descriptor.name in self._tools:
                raise ValueError(f"Tool already registered: {tool.descriptor.name}")
            self._tools[tool.descriptor.name] = tool
        return tool

    def unregister(self, name: str) -> Tool:
        """Remove one tool without executing or closing it implicitly."""
        with self._lock:
            try:
                return self._tools.pop(name)
            except KeyError as error:
                raise ToolNotFoundError(f"Tool not registered: {name}") from error

    def lookup(self, name: str) -> Tool:
        """Return one explicitly registered tool or a clear SDK error."""
        with self._lock:
            try:
                return self._tools[name]
            except KeyError as error:
                raise ToolNotFoundError(f"Tool not registered: {name}") from error

    def list(self) -> tuple[Tool, ...]:
        """Return a stable name-sorted snapshot of the local registry."""
        with self._lock:
            return tuple(self._tools[name] for name in sorted(self._tools))

    def clear(self) -> None:
        """Clear explicitly registered local tools for test or app cleanup."""
        with self._lock:
            self._tools.clear()


default_registry = ToolRegistry()
