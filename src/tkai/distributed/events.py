"""Immutable shared EventBus events for local distributed-runtime activity."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True)
class DistributedEvent(Event):
    """Base event containing safe node, lock, or coordinator metadata."""

    subject: str = ""


@dataclass(frozen=True, slots=True)
class NodeJoined(DistributedEvent):
    name: str = field(default="NodeJoined", init=False)


@dataclass(frozen=True, slots=True)
class NodeLeft(DistributedEvent):
    name: str = field(default="NodeLeft", init=False)


@dataclass(frozen=True, slots=True)
class HeartbeatUpdated(DistributedEvent):
    name: str = field(default="HeartbeatUpdated", init=False)


@dataclass(frozen=True, slots=True)
class LockAcquired(DistributedEvent):
    name: str = field(default="LockAcquired", init=False)


@dataclass(frozen=True, slots=True)
class LockReleased(DistributedEvent):
    name: str = field(default="LockReleased", init=False)


@dataclass(frozen=True, slots=True)
class CoordinatorStarted(DistributedEvent):
    name: str = field(default="CoordinatorStarted", init=False)


@dataclass(frozen=True, slots=True)
class CoordinatorStopped(DistributedEvent):
    name: str = field(default="CoordinatorStopped", init=False)
