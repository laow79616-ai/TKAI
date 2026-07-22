"""Cooperative runtime control signals."""

from __future__ import annotations

from enum import Enum, auto


class ExecutionState(Enum):
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    CANCELLED = auto()
    FINISHED = auto()
