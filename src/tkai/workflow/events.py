"""Workflow event primitives."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """An immutable event emitted while executing a workflow."""

    name: str
    payload: dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], None]


class EventBus:
    """Publish workflow lifecycle events to in-process subscribers."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """Subscribe ``handler`` to an event name."""
        self._handlers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> None:
        """Remove an existing subscription, if present."""
        handlers = self._handlers.get(event_name)
        if handlers is not None and handler in handlers:
            handlers.remove(handler)

    def emit(self, event: Event) -> None:
        """Synchronously notify handlers registered for ``event``."""
        for handler in tuple(self._handlers.get(event.name, ())):
            handler(event)
