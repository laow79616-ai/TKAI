"""Scheduler contracts without a background runtime."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol


class Scheduler(Protocol):
    """Schedules work through an implementation supplied by a module."""

    def submit(self, callback: Callable[[], object]) -> str: ...


__all__ = ("Scheduler",)
