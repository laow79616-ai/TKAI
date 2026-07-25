"""Framework-neutral trace adapter."""

from .models import Event, TraceContext
from .subscriber import Subscriber


class TraceAdapter(Subscriber):
    def __init__(self) -> None:
        self.spans: list[TraceContext] = []

    def supports(self, event: Event) -> bool:
        return event.trace_id is not None

    def handle(self, event: Event) -> None:
        self.spans.append(TraceContext(event.trace_id or "", event.name))
