"""Structured in-memory JSON logger adapter."""

import json

from .models import Event
from .subscriber import Subscriber


class LoggerAdapter(Subscriber):
    def __init__(self) -> None:
        self.records: list[str] = []

    def supports(self, event: Event) -> bool:
        return True

    def handle(self, event: Event) -> None:
        self.records.append(
            json.dumps(
                {
                    "event": event.name,
                    "trace_id": event.trace_id,
                    "correlation_id": event.correlation_id,
                },
                sort_keys=True,
            )
        )
