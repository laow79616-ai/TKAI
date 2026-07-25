"""Immutable observability events for optional policy execution."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True)
class PolicyEvent(Event):
    """Base event carrying safe policy name and stage metadata."""

    policy: str = ""
    stage: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class PolicyExecuted(PolicyEvent):
    """Emitted after a policy has evaluated and applied successfully."""

    name: str = field(default="PolicyExecuted", init=False)


@dataclass(frozen=True, slots=True)
class PolicyFailed(PolicyEvent):
    """Emitted when a policy raises and execution is safely isolated."""

    name: str = field(default="PolicyFailed", init=False)


@dataclass(frozen=True, slots=True)
class PolicySkipped(PolicyEvent):
    """Emitted when a policy is disabled or evaluation rejects its context."""

    name: str = field(default="PolicySkipped", init=False)
