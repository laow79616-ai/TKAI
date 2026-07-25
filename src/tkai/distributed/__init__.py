"""Optional distributed backends; local memory remains the default."""

from .backend import DistributedBackend, LocalBackend, LocalMemoryBackend
from .coordinator import DistributedCoordinator, LocalCoordinator
from .discovery import (
    LocalServiceRegistry,
    RedisServiceRegistry,
    ServiceInstance,
    ServiceRegistry,
)
from .errors import (
    DistributedError,
    DistributedLockError,
    FailoverStateError,
    NodeNotFoundError,
    RedisBackendConnectionError,
    RedisBackendError,
    RedisBackendOperationError,
    RedisBackendUnavailableError,
    ServiceInstanceNotFoundError,
    ServiceRegistryError,
)
from .events import (
    BackendFailedBack,
    BackendFailedOver,
    CoordinatorStarted,
    CoordinatorStopped,
    DistributedEvent,
    HeartbeatUpdated,
    LockAcquired,
    LockReleased,
    NodeJoined,
    NodeLeft,
    PrimaryBackendRecovered,
)
from .factory import BackendConfig, BackendFactory, create_backend
from .failover import (
    BackendPriority,
    FailoverBackend,
    FailoverConfig,
    FailoverManager,
    FailoverMetrics,
    FailoverSnapshot,
    FailoverState,
)
from .health import (
    BackendHealthChecker,
    BackendHealthSnapshot,
    BackendHealthStatus,
    HealthChecker,
    HealthProbeConfig,
    ProbeableBackend,
)
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
    "BackendFailedBack",
    "BackendFailedOver",
    "BackendHealthChecker",
    "BackendHealthSnapshot",
    "BackendHealthStatus",
    "BackendPriority",
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
    "FailoverBackend",
    "FailoverConfig",
    "FailoverManager",
    "FailoverMetrics",
    "FailoverSnapshot",
    "FailoverState",
    "FailoverStateError",
    "Heartbeat",
    "HeartbeatSnapshot",
    "HeartbeatUpdated",
    "LocalBackend",
    "LocalMemoryBackend",
    "LocalServiceRegistry",
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
    "HealthChecker",
    "HealthProbeConfig",
    "ProbeableBackend",
    "PrimaryBackendRecovered",
    "RedisBackend",
    "RedisBackendConnectionError",
    "RedisBackendError",
    "RedisBackendOperationError",
    "RedisBackendUnavailableError",
    "RedisClient",
    "RedisServiceRegistry",
    "ServiceInstance",
    "ServiceInstanceNotFoundError",
    "ServiceRegistry",
    "ServiceRegistryError",
    "create_backend",
)
