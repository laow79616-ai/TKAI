"""Priority, delayed, scheduled, and dead-letter queues."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field


@dataclass(order=True, slots=True)
class QueueItem:
    available_at: float
    negative_priority: int
    sequence: int
    execution_id: str = field(compare=False)


class ExecutionQueue:
    def __init__(self) -> None:
        self._items: list[QueueItem] = []
        self._dead: list[str] = []
        self._sequence = 0

    def put(self, execution_id: str, priority: int, available_at: float = 0) -> None:
        self._sequence += 1
        heapq.heappush(
            self._items,
            QueueItem(available_at, -priority, self._sequence, execution_id),
        )

    def pop(self, now: float) -> str | None:
        if not self._items or self._items[0].available_at > now:
            return None
        return heapq.heappop(self._items).execution_id

    def dead_letter(self, execution_id: str) -> None:
        self._dead.append(execution_id)

    @property
    def depth(self) -> int:
        return len(self._items)

    @property
    def dead_letters(self) -> tuple[str, ...]:
        return tuple(self._dead)
