"""Immutable EventBus events for explicit local retry execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True)
class RetryEvent(Event):
    """Base retry event containing only safe policy and attempt metadata."""

    policy: str = ""
    attempt: int = 0
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RetryScheduled(RetryEvent):
    """Emitted when an explicit manager will retry after a local delay."""

    name: str = field(default="RetryScheduled", init=False)


@dataclass(frozen=True, slots=True)
class RetryExhausted(RetryEvent):
    """Emitted when an operation will not receive another retry."""

    name: str = field(default="RetryExhausted", init=False)
