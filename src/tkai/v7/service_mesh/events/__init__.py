"""In-process service mesh event hooks."""

from __future__ import annotations

from collections.abc import Callable, Mapping


class ServiceEventBus:
    def __init__(self) -> None:
        self._subscribers: list[Callable[[Mapping[str, object]], None]] = []

    def subscribe(self, callback: Callable[[Mapping[str, object]], None]) -> None:
        self._subscribers.append(callback)

    def publish(self, event: Mapping[str, object]) -> None:
        for callback in tuple(self._subscribers):
            callback(event)


__all__ = ("ServiceEventBus",)
