"""Provider-independent async runtime lifecycle infrastructure."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from enum import Enum, auto
from typing import Any, Protocol


class LifecycleState(Enum):
    CREATED = auto()
    INITIALIZING = auto()
    INITIALIZED = auto()
    ACTIVE = auto()
    DEGRADED = auto()
    CLOSING = auto()
    CLOSED = auto()


class OwnershipPolicy(Enum):
    RUNTIME_OWNED = auto()
    EXTERNALLY_OWNED = auto()

    def should_close(self) -> bool:
        return self is OwnershipPolicy.RUNTIME_OWNED


class RuntimeLifecycleError(RuntimeError):
    pass


class AsyncTransport(Protocol):
    async def request(self, method: str, url: str, **kwargs: Any) -> Any: ...
    def stream(self, method: str, url: str, **kwargs: Any) -> AsyncIterator[bytes]: ...
    async def close(self) -> None: ...
    def health_check(self) -> bool: ...


class RetryPolicy:
    def __init__(self, max_retries: int = 0) -> None:
        self.max_retries = max_retries


class RetryExecutor:
    def __init__(self, policy: RetryPolicy) -> None:
        self.policy = policy


class ProviderRuntime:
    def __init__(
        self,
        transport: AsyncTransport,
        *,
        ownership: OwnershipPolicy = OwnershipPolicy.EXTERNALLY_OWNED,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.transport = transport
        self.ownership = ownership
        self.retry = RetryExecutor(retry_policy or RetryPolicy())
        self.state = LifecycleState.CREATED

    async def initialize(self) -> None:
        if self.state in (LifecycleState.INITIALIZED, LifecycleState.ACTIVE):
            return
        if self.state is LifecycleState.CLOSED:
            raise RuntimeLifecycleError("runtime is closed")
        self.state = LifecycleState.INITIALIZING
        self.state = LifecycleState.INITIALIZED

    @asynccontextmanager
    async def request_scope(self) -> AsyncIterator[AsyncTransport]:
        await self.initialize()
        self.state = LifecycleState.ACTIVE
        try:
            yield self.transport
        finally:
            if self.state is LifecycleState.ACTIVE:
                self.state = LifecycleState.INITIALIZED

    async def close(self) -> None:
        if self.state is LifecycleState.CLOSED:
            return
        self.state = LifecycleState.CLOSING
        if self.ownership.should_close():
            await self.transport.close()
        self.state = LifecycleState.CLOSED

    def health(self) -> dict[str, Any]:
        return {
            "lifecycle": self.state.name.lower(),
            "transport_available": self.transport.health_check(),
            "retry_enabled": self.retry.policy.max_retries > 0,
            "owner": self.ownership.name.lower(),
        }
