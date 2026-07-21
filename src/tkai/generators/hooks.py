"""
TKAI Generator Hooks
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from typing import Callable

Hook = Callable[..., Any]


class HookManager:
    """Manage generator lifecycle hooks."""

    def __init__(self) -> None:
        self._hooks: dict[str, list[Hook]] = defaultdict(list)

    def register(
        self,
        event: str,
        func: Hook,
    ) -> None:
        """Register a hook."""
        self._hooks[event].append(func)

    def unregister(
        self,
        event: str,
        func: Hook,
    ) -> None:
        """Remove a hook."""
        if event not in self._hooks:
            return

        if func in self._hooks[event]:
            self._hooks[event].remove(func)

    def clear(
        self,
        event: str | None = None,
    ) -> None:
        """Clear hooks."""
        if event is None:
            self._hooks.clear()
            return

        self._hooks.pop(event, None)

    def run(
        self,
        event: str,
        *args,
        **kwargs,
    ) -> list[Any]:
        """Run hooks."""
        results = []

        for hook in self._hooks.get(event, []):
            results.append(
                hook(*args, **kwargs)
            )

        return results

    def has(self, event: str) -> bool:
        return bool(self._hooks.get(event))

    def events(self) -> list[str]:
        return sorted(self._hooks.keys())