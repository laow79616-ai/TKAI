"""Thread-safe local membership with explicit heartbeat and expiry simulation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from threading import RLock

from tkai.observability import EventBus

from .errors import NodeNotFoundError
from .events import HeartbeatUpdated, NodeJoined, NodeLeft
from .models import Node, NodeStatus


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Membership:
    """Maintain local node snapshots without discovery, gossip, or network I/O."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self._nodes: dict[str, Node] = {}
        self._lock = RLock()
        self.event_bus = event_bus

    def register(self, node: Node) -> Node:
        """Register or replace one local node and publish a join event."""
        with self._lock:
            self._nodes[node.node_id] = node
        self._publish(NodeJoined(subject=node.node_id))
        return node

    def unregister(self, node_id: str) -> Node:
        """Remove one node and publish a leave event."""
        with self._lock:
            try:
                node = self._nodes.pop(node_id)
            except KeyError as error:
                raise NodeNotFoundError(
                    f"Node '{node_id}' is not registered"
                ) from error
        self._publish(NodeLeft(subject=node_id))
        return node

    def heartbeat(self, node_id: str, *, now: datetime | None = None) -> Node:
        """Update last-seen state for one registered local node."""
        current = now or _utc_now()
        with self._lock:
            try:
                node = self._nodes[node_id]
            except KeyError as error:
                raise NodeNotFoundError(
                    f"Node '{node_id}' is not registered"
                ) from error
            updated = Node(
                node.node_id,
                node.hostname,
                node.started_at,
                current,
                node.capabilities,
                NodeStatus.ACTIVE,
            )
            self._nodes[node_id] = updated
        self._publish(HeartbeatUpdated(subject=node_id))
        return updated

    def snapshot(
        self, *, expiry: timedelta | None = None, now: datetime | None = None
    ) -> list[Node]:
        """Return stable snapshots and optionally mark stale nodes expired locally."""
        current = now or _utc_now()
        with self._lock:
            if expiry is not None:
                for node_id, node in tuple(self._nodes.items()):
                    if (
                        current - node.last_seen > expiry
                        and node.status is not NodeStatus.EXPIRED
                    ):
                        self._nodes[node_id] = Node(
                            node.node_id,
                            node.hostname,
                            node.started_at,
                            node.last_seen,
                            node.capabilities,
                            NodeStatus.EXPIRED,
                        )
            return [self._nodes[node_id] for node_id in sorted(self._nodes)]

    def _publish(self, event: NodeJoined | NodeLeft | HeartbeatUpdated) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(event)
