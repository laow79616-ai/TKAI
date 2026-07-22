"""Stable dependency-ready dispatch queue."""

from __future__ import annotations

from .task import Step


class Dispatcher:
    def __init__(self, steps: list[Step], completed: set[str] | None = None) -> None:
        self.pending = list(steps)
        self.completed = completed or set()
        self.in_flight: set[str] = set()

    def next_ready(self) -> list[Step]:
        return [
            step
            for step in self.pending
            if (
                set(step.dependency_names) <= self.completed
                and (step.name or step.task.name) not in self.in_flight
            )
        ]

    def claim(self, step: Step) -> None:
        """Reserve a ready step so it cannot be scheduled twice."""
        name = step.name or step.task.name
        if step not in self.pending or name in self.in_flight:
            raise ValueError(f"Step '{name}' is not available for dispatch")
        self.in_flight.add(name)

    def mark_complete(self, step: Step) -> None:
        self.pending.remove(step)
        name = step.name or step.task.name
        self.in_flight.discard(name)
        self.completed.add(name)

    def mark_terminal(self, step: Step) -> None:
        """Remove a failed or cancelled step without satisfying dependencies."""
        self.pending.remove(step)
        self.in_flight.discard(step.name or step.task.name)

    def cancel_waiting(self) -> list[Step]:
        """Remove all not-yet-running steps and return them in stable order."""
        waiting = [
            step
            for step in self.pending
            if (step.name or step.task.name) not in self.in_flight
        ]
        for step in waiting:
            self.pending.remove(step)
        return waiting

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
        self.in_flight.clear()
