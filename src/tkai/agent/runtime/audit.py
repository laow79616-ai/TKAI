"""Immutable local audit log for agent control actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock


class AgentAuditAction(str, Enum):
    CREATE = "create"
    RUN = "run"
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class AgentAuditEvent:
    sequence: int
    action: AgentAuditAction
    identifier: str
    timestamp: str
    actor: str | None = None


class AgentAuditLog:
    def __init__(self) -> None:
        self._events: list[AgentAuditEvent] = []
        self._lock = RLock()

    def record(
        self,
        action: AgentAuditAction,
        identifier: str,
        timestamp: str,
        actor: str | None = None,
    ) -> AgentAuditEvent:
        with self._lock:
            event = AgentAuditEvent(
                len(self._events) + 1, action, identifier, timestamp, actor
            )
            self._events.append(event)
            return event

    def list(self) -> tuple[AgentAuditEvent, ...]:
        with self._lock:
            return tuple(self._events)

