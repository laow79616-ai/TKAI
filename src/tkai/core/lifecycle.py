"""
TKAI Core Lifecycle

Application lifecycle manager.
"""

from __future__ import annotations

from enum import Enum, auto


class LifecycleState(Enum):
    """Lifecycle states."""

    CREATED = auto()
    INITIALIZED = auto()
    STARTED = auto()
    STOPPED = auto()
    DISPOSED = auto()


class Lifecycle:
    """Application lifecycle."""

    def __init__(self) -> None:
        self._state = LifecycleState.CREATED

    @property
    def state(self) -> LifecycleState:
        """Current lifecycle state."""
        return self._state

    def initialize(self) -> None:
        """Initialize application."""
        self._state = LifecycleState.INITIALIZED

    def start(self) -> None:
        """Start application."""
        self._state = LifecycleState.STARTED

    def stop(self) -> None:
        """Stop application."""
        self._state = LifecycleState.STOPPED

    def dispose(self) -> None:
        """Dispose application."""
        self._state = LifecycleState.DISPOSED

    @property
    def is_created(self) -> bool:
        return self._state is LifecycleState.CREATED

    @property
    def is_initialized(self) -> bool:
        return self._state is LifecycleState.INITIALIZED

    @property
    def is_started(self) -> bool:
        return self._state is LifecycleState.STARTED

    @property
    def is_stopped(self) -> bool:
        return self._state is LifecycleState.STOPPED

    @property
    def is_disposed(self) -> bool:
        return self._state is LifecycleState.DISPOSED