"""In-memory metrics adapter."""

from .models import Event
from .subscriber import Subscriber


class MetricsAdapter(Subscriber):
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}

    def supports(self, event: Event) -> bool:
        return True

    def handle(self, event: Event) -> None:
        self.counts[event.name] = self.counts.get(event.name, 0) + 1
