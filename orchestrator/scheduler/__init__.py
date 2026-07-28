"""Scheduled and delayed execution support."""

from time import time

from ..queue import ExecutionQueue


class Scheduler:
    def __init__(self, queue: ExecutionQueue) -> None:
        self.queue = queue

    def schedule(
        self, execution_id: str, priority: int, delay_seconds: float = 0
    ) -> None:
        self.queue.put(execution_id, priority, time() + max(0, delay_seconds))
