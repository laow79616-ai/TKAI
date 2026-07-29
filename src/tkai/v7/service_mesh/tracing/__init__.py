"""Transport-neutral tracing hooks."""

from __future__ import annotations

from collections.abc import Callable, Mapping


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(
        self, hook: Callable[[str, Mapping[str, object]], None]
    ) -> None:
        self._hooks.append(hook)

    def emit(self, event: str, attributes: Mapping[str, object]) -> None:
        for hook in tuple(self._hooks):
            hook(event, attributes)


__all__ = ("TracingHooks",)
