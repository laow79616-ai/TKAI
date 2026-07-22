"""Framework-neutral in-memory event bus."""

from __future__ import annotations

from collections.abc import Callable

from .models import Event


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[Callable[[Event], None]] = []
        self.events: list[Event] = []

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        if handler not in self._handlers:
            self._handlers.append(handler)

    def unsubscribe(self, handler: Callable[[Event], None]) -> None:
        if handler in self._handlers:
            self._handlers.remove(handler)

    def publish(self, event: Event) -> None:
        self.events.append(event)
        for handler in tuple(self._handlers):
            handler(event)

    def clear(self) -> None:
        self.events.clear()
        self._handlers.clear()
