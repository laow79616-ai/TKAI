"""Explicit errors for the optional local Distributed Runtime foundation."""


class DistributedError(RuntimeError):
    """Base error for distributed backend, membership, and lock operations."""


class DistributedLockError(DistributedError):
    """Raised when a local distributed lock cannot be acquired or released."""


class NodeNotFoundError(DistributedError):
    """Raised when a membership node is absent."""


class RedisBackendError(DistributedError):
    """Base error raised by the optional Redis distributed backend."""


class RedisBackendUnavailableError(RedisBackendError):
    """Raised when Redis support is requested without its optional dependency."""


class RedisBackendConnectionError(RedisBackendError):
    """Raised when the Redis backend cannot establish a usable connection."""


class RedisBackendOperationError(RedisBackendError):
    """Raised when a Redis backend operation cannot complete safely."""
