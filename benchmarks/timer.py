"""Small, strict lifecycle wrapper around :func:`time.perf_counter_ns`."""

from __future__ import annotations

from time import perf_counter_ns


class TimerStateError(RuntimeError):
    """Raised when a high-resolution timer is used outside its lifecycle."""


class HighResolutionTimer:
    """Measure elapsed wall-clock time without sleeping or external dependencies."""

    def __init__(self) -> None:
        self._started_ns: int | None = None
        self._stopped_ns: int | None = None

    def start(self) -> HighResolutionTimer:
        """Begin one measurement; a running timer cannot be restarted."""
        if self._started_ns is not None and self._stopped_ns is None:
            raise TimerStateError("timer is already running")
        self._started_ns = perf_counter_ns()
        self._stopped_ns = None
        return self

    def stop(self) -> int:
        """End a running measurement and return the elapsed nanoseconds."""
        if self._started_ns is None:
            raise TimerStateError("timer has not been started")
        if self._stopped_ns is not None:
            raise TimerStateError("timer has already been stopped")
        self._stopped_ns = perf_counter_ns()
        return self.elapsed_ns

    @property
    def elapsed_ns(self) -> int:
        """Return elapsed nanoseconds only after a completed measurement."""
        if self._started_ns is None or self._stopped_ns is None:
            raise TimerStateError("timer has not completed")
        return self._stopped_ns - self._started_ns

    @property
    def elapsed_seconds(self) -> float:
        """Return elapsed seconds derived exactly from the nanosecond duration."""
        return self.elapsed_ns / 1_000_000_000
