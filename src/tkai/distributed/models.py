"""Immutable local distributed-runtime models with UTC-safe serialization."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum


class NodeStatus(str, Enum):
    """Local membership state; no leader election is implied."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Node:
    """One local membership node suitable for safe diagnostics."""

    node_id: str
    hostname: str
    started_at: datetime
    last_seen: datetime
    capabilities: frozenset[str] = frozenset()
    status: NodeStatus = NodeStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.node_id or not self.hostname:
            raise ValueError("node_id and hostname must not be empty")
        for name in ("started_at", "last_seen"):
            value = getattr(self, name)
            if value.tzinfo is None:
                raise ValueError(f"{name} must be timezone-aware")
            object.__setattr__(self, name, value.astimezone(timezone.utc))

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-ready membership metadata."""
        data = asdict(self)
        data["capabilities"] = sorted(self.capabilities)
        data["status"] = self.status.value
        data["started_at"] = self.started_at.isoformat()
        data["last_seen"] = self.last_seen.isoformat()
        return data


@dataclass(frozen=True, slots=True)
class LockSnapshot:
    """Read-only local lock state for diagnostics without exposing mutexes."""

    name: str
    owner: str | None = None
    acquired: bool = False
    expires_at: datetime | None = None

    def to_dict(self) -> dict[str, object]:
        """Return stable lock metadata with UTC timestamp strings."""
        return {
            "name": self.name,
            "owner": self.owner,
            "acquired": self.acquired,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
        }


@dataclass(frozen=True, slots=True)
class HeartbeatSnapshot:
    """State of an explicitly started local heartbeat controller."""

    node_id: str
    running: bool = False
    last_beat: datetime | None = None

    def to_dict(self) -> dict[str, object]:
        """Return JSON-ready heartbeat state."""
        return {
            "node_id": self.node_id,
            "running": self.running,
            "last_beat": self.last_beat.isoformat() if self.last_beat else None,
        }
