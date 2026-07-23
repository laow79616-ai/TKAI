"""Optional distributed backends; local memory remains the default."""

from .backend import DistributedBackend, LocalBackend, LocalMemoryBackend
from .coordinator import DistributedCoordinator, LocalCoordinator
from .errors import (
    DistributedError,
    DistributedLockError,
    NodeNotFoundError,
    RedisBackendConnectionError,
    RedisBackendError,
    RedisBackendOperationError,
    RedisBackendUnavailableError,
)
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
from .factory import BackendConfig, BackendFactory, create_backend
from .heartbeat import Heartbeat
from .locks import DistributedLock, LocalLock
from .membership import Membership
from .models import HeartbeatSnapshot, LockSnapshot, Node, NodeStatus
from .redis import RedisBackend, RedisClient
from .registry import DistributedRegistry
from .runtime_adapter import DistributedPolicyAdapter, DistributedRuntimeAdapter

__all__ = (
    "BackendConfig",
    "BackendFactory",
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
    "LocalMemoryBackend",
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
    "RedisBackend",
    "RedisBackendConnectionError",
    "RedisBackendError",
    "RedisBackendOperationError",
    "RedisBackendUnavailableError",
    "RedisClient",
    "create_backend",
)
