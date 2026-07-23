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


@dataclass(frozen=True, slots=True)
class BackendFailedOver(DistributedEvent):
    """Published when an explicit manager activates its secondary backend."""

    name: str = field(default="BackendFailedOver", init=False)


@dataclass(frozen=True, slots=True)
class PrimaryBackendRecovered(DistributedEvent):
    """Published after the primary reaches its configured recovery threshold."""

    name: str = field(default="PrimaryBackendRecovered", init=False)


@dataclass(frozen=True, slots=True)
class BackendFailedBack(DistributedEvent):
    """Published after an explicit manual failback activates the primary."""

    name: str = field(default="BackendFailedBack", init=False)
