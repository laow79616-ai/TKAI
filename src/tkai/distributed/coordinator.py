"""Explicit local coordinator; it never automatically owns framework services."""

from __future__ import annotations

from datetime import datetime, timezone

from tkai.observability import EventBus

from .backend import DistributedBackend, LocalBackend
from .events import CoordinatorStarted, CoordinatorStopped
from .heartbeat import Heartbeat
from .locks import LocalLock
from .membership import Membership
from .models import Node
from .registry import DistributedRegistry


class DistributedCoordinator:
    """Coordinate supplied local services through one explicit LocalBackend."""

    def __init__(
        self,
        node: Node,
        *,
        backend: DistributedBackend | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self.node = node
        self.backend = backend or LocalBackend()
        self.event_bus = event_bus
        self.membership = Membership(event_bus=event_bus)
        self.heartbeat = Heartbeat(self.membership, node.node_id)
        self.registry = DistributedRegistry()
        self._started = False

    def start(self) -> None:
        """Connect locally, register this node, and start cooperative heartbeat."""
        if self._started:
            return
        self.backend.connect()
        self.membership.register(self.node)
        self.heartbeat.start()
        self._started = True
        self._publish(CoordinatorStarted(subject=self.node.node_id))

    def stop(self) -> None:
        """Stop heartbeat and disconnect locally without changing external services."""
        if not self._started:
            return
        self.heartbeat.stop()
        try:
            self.membership.unregister(self.node.node_id)
        finally:
            self.backend.disconnect()
            self._started = False
        self._publish(CoordinatorStopped(subject=self.node.node_id))

    def lock(self, name: str) -> LocalLock:
        """Create an explicit local lock scoped to this coordinator node."""
        return LocalLock(
            self.backend, name, self.node.node_id, event_bus=self.event_bus
        )

    def register_resource(self, name: str, resource: object) -> None:
        """Retain an application-owned resource reference for diagnostics only."""
        self.registry.register(name, resource)

    def summary(self) -> dict[str, object]:
        """Return safe local coordinator diagnostics without probing a network."""
        return {
            "backend": type(self.backend).__name__,
            "started": self._started,
            "healthy": self.backend.health(),
            "nodes": [node.to_dict() for node in self.membership.snapshot()],
            "heartbeat": self.heartbeat.snapshot().to_dict(),
            "resources": self.registry.list(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _publish(self, event: CoordinatorStarted | CoordinatorStopped) -> None:
        if self.event_bus is not None:
            self.event_bus.publish(event)


LocalCoordinator = DistributedCoordinator
