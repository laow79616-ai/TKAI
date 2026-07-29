"""Extensions may register contracts only; transports and networks are excluded."""

from typing import Protocol

from ..framework import EventRegistry


class EventFabricExtension(Protocol):
    def register(self, registry: EventRegistry) -> None: ...


__all__ = ("EventFabricExtension",)
