"""Framework-neutral in-memory event bus."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock

from .models import Event


class EventBus:
    def __init__(self) -> None:
        self._handlers: list[Callable[[Event], None]] = []
        self.events: list[Event] = []
        self._lock = RLock()

    def subscribe(self, handler: Callable[[Event], None]) -> None:
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def unsubscribe(self, handler: Callable[[Event], None]) -> None:
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def publish(self, event: Event) -> None:
        with self._lock:
            self.events.append(event)
            handlers = tuple(self._handlers)
        for handler in handlers:
            handler(event)

    def clear(self) -> None:
        with self._lock:
            self.events.clear()
            self._handlers.clear()
