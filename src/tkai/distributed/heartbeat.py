"""Explicit, cooperative local heartbeat controller without background threads."""

from __future__ import annotations

from datetime import datetime, timezone

from .membership import Membership
from .models import HeartbeatSnapshot


class Heartbeat:
    """Update one registered node only when start or beat is explicitly called."""

    def __init__(self, membership: Membership, node_id: str) -> None:
        self.membership = membership
        self.node_id = node_id
        self._running = False
        self._last_beat: datetime | None = None

    def start(self) -> HeartbeatSnapshot:
        """Start cooperative heartbeat state and perform one immediate local beat."""
        self._running = True
        return self.beat()

    def stop(self) -> HeartbeatSnapshot:
        """Stop cooperative heartbeats without changing membership ownership."""
        self._running = False
        return self.snapshot()

    def beat(self) -> HeartbeatSnapshot:
        """Perform one explicit membership heartbeat when running."""
        if self._running:
            self._last_beat = datetime.now(timezone.utc)
            self.membership.heartbeat(self.node_id, now=self._last_beat)
        return self.snapshot()

    def snapshot(self) -> HeartbeatSnapshot:
        """Return immutable current heartbeat controller state."""
        return HeartbeatSnapshot(self.node_id, self._running, self._last_beat)
