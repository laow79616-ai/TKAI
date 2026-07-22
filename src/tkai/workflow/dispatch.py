"""Stable dependency-ready dispatch queue."""

from __future__ import annotations

from .task import Step


class Dispatcher:
    def __init__(self, steps: list[Step], completed: set[str] | None = None) -> None:
        self.pending = list(steps)
        self.completed = completed or set()

    def next_ready(self) -> list[Step]:
        return [
            step
            for step in self.pending
            if set(step.dependency_names) <= self.completed
        ]

    def mark_complete(self, step: Step) -> None:
        self.pending.remove(step)
        self.completed.add(step.name or step.task.name)

    def mark_terminal(self, step: Step) -> None:
        """Remove a failed or cancelled step without satisfying dependencies."""
        self.pending.remove(step)

    def restore(self, terminal: set[str], satisfied: set[str]) -> None:
        """Rebuild pending work while preserving definition order.

        ``terminal`` removes all terminal work. Only ``satisfied`` (completed
        and skipped steps) is permitted to unblock a dependent step.
        """
        self.pending = [
            step
            for step in self.pending
            if (step.name or step.task.name) not in terminal
        ]
        self.completed = set(satisfied)
