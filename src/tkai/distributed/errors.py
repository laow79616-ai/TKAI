"""Explicit errors for the optional local Distributed Runtime foundation."""


class DistributedError(RuntimeError):
    """Base error for distributed backend, membership, and lock operations."""


class DistributedLockError(DistributedError):
    """Raised when a local distributed lock cannot be acquired or released."""


class NodeNotFoundError(DistributedError):
    """Raised when a membership node is absent."""
