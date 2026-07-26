"""In-process execution event stream."""

from collections import defaultdict
from collections.abc import Callable
from typing import Any


class EventBus:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []
        self._subscribers: dict[str, list[Callable[[dict[str, Any]], None]]] = (
            defaultdict(list)
        )

    def subscribe(self, name: str, handler: Callable[[dict[str, Any]], None]) -> None:
        self._subscribers[name].append(handler)

    def publish(self, name: str, **payload: Any) -> None:
        event = {"name": name, **payload}
        self.events.append(event)
        for handler in self._subscribers[name]:
            handler(event)
