"""Synchronous in-process event hooks used by the foundation."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class Event:
    """Immutable structured kernel event."""

    name: str
    payload: dict[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


EventHandler = Callable[[Event], None]


class EventBus:
    """Deterministic local event bus with no transport side effects."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, name: str, handler: EventHandler) -> None:
        self._handlers[name].append(handler)

    def publish(self, event: Event) -> None:
        for handler in tuple(self._handlers.get(event.name, ())):
            handler(event)


__all__ = ("Event", "EventBus", "EventHandler")
