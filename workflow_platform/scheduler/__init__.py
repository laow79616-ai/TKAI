"""Bounded in-process schedule registry."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Schedule:
    id: str
    workflow_id: str
    run_at: datetime
    recurring: str | None = None


class Scheduler:
    def __init__(self, limit: int = 1000) -> None:
        self.limit = limit
        self.items: dict[str, Schedule] = {}

    def add(self, schedule: Schedule) -> None:
        if len(self.items) >= self.limit:
            raise ValueError("Schedule limit exceeded.")
        self.items[schedule.id] = schedule
