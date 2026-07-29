"""In-process capability events."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class CapabilityEvent:
    name: str
    capability_id: str
    payload: Mapping[str, object]


class CapabilityEventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[CapabilityEvent], None]]] = (
            defaultdict(list)
        )

    def subscribe(self, name: str, callback: Callable[[CapabilityEvent], None]) -> None:
        self._subscribers[name].append(callback)

    def publish(self, event: CapabilityEvent) -> None:
        for callback in tuple(self._subscribers.get(event.name, ())):
            callback(event)


__all__ = ("CapabilityEvent", "CapabilityEventBus")
