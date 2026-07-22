"""Subscriber dispatcher."""

from .models import Event
from .subscriber import Subscriber


class EventDispatcher:
    def __init__(self, subscribers: list[Subscriber] | None = None) -> None:
        self.subscribers = subscribers or []

    def dispatch(self, event: Event) -> None:
        for subscriber in tuple(self.subscribers):
            if subscriber.supports(event):
                subscriber.handle(event)
