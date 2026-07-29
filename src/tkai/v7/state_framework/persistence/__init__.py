"""Optional persistence adapters; the framework performs no implicit I/O."""

from __future__ import annotations

from ..contracts import StateRecord


class MemoryStatePersistence:
    def __init__(self) -> None:
        self._states: dict[str, StateRecord] = {}

    def save(self, state: StateRecord) -> None:
        self._states[state.state_id] = state

    def load(self, state_id: str) -> StateRecord | None:
        return self._states.get(state_id)


__all__ = ("MemoryStatePersistence",)
