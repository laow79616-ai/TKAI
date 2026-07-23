"""Optional local Distributed Runtime foundation with no network backends."""

from .backend import DistributedBackend, LocalBackend
from .coordinator import DistributedCoordinator, LocalCoordinator
from .errors import DistributedError, DistributedLockError, NodeNotFoundError
from .events import (
    CoordinatorStarted,
    CoordinatorStopped,
    DistributedEvent,
    HeartbeatUpdated,
    LockAcquired,
    LockReleased,
    NodeJoined,
    NodeLeft,
)
from .heartbeat import Heartbeat
from .locks import DistributedLock, LocalLock
from .membership import Membership
from .models import HeartbeatSnapshot, LockSnapshot, Node, NodeStatus
from .registry import DistributedRegistry
from .runtime_adapter import DistributedPolicyAdapter, DistributedRuntimeAdapter

__all__ = (
    "CoordinatorStarted",
    "CoordinatorStopped",
    "DistributedBackend",
    "DistributedCoordinator",
    "DistributedError",
    "DistributedEvent",
    "DistributedLock",
    "DistributedLockError",
    "DistributedPolicyAdapter",
    "DistributedRegistry",
    "DistributedRuntimeAdapter",
    "Heartbeat",
    "HeartbeatSnapshot",
    "HeartbeatUpdated",
    "LocalBackend",
    "LocalCoordinator",
    "LocalLock",
    "LockAcquired",
    "LockReleased",
    "LockSnapshot",
    "Membership",
    "Node",
    "NodeJoined",
    "NodeLeft",
    "NodeNotFoundError",
    "NodeStatus",
)
