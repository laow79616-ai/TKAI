"""Optional Redis implementation of the explicit distributed backend contract.

The module intentionally imports ``redis`` only when a caller connects without
injecting a client.  This keeps Redis an optional dependency and keeps normal
TKAI imports, local development, and offline tests network-free.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from importlib import import_module
from threading import RLock
from typing import Any, Protocol, cast

from .errors import (
    RedisBackendConnectionError,
    RedisBackendOperationError,
    RedisBackendUnavailableError,
)


class RedisClient(Protocol):
    """Small synchronous Redis-client surface used by :class:`RedisBackend`."""

    def ping(self) -> bool: ...
    def get(self, key: str) -> bytes | str | None: ...
    def set(
        self, key: str, value: str, *, nx: bool = False, ex: int | None = None
    ) -> Any: ...
    def delete(self, key: str) -> int: ...
    def publish(self, topic: str, value: str) -> int: ...
    def close(self) -> None: ...


class RedisBackend:
    """Explicit Redis backend with injected-client support and bounded retries.

    Values and messages are JSON encoded deliberately; arbitrary Python object
    serialization is avoided because it would require unsafe deserialization.
    Subscription callbacks retain the existing in-process backend contract.
    Remote Redis pub/sub consumption is intentionally not started implicitly.
    """

    def __init__(
        self,
        *,
        url: str = "redis://localhost:6379/0",
        namespace: str = "tkai",
        timeout_seconds: float = 5.0,
        reconnect_attempts: int = 1,
        lock_ttl_seconds: int = 30,
        client: RedisClient | None = None,
    ) -> None:
        """Configure a backend without importing Redis or opening a connection."""
        if not url:
            raise ValueError("Redis URL must not be empty.")
        if not namespace:
            raise ValueError("Redis namespace must not be empty.")
        if timeout_seconds <= 0:
            raise ValueError("Redis timeout_seconds must be greater than zero.")
        if reconnect_attempts < 0:
            raise ValueError("Redis reconnect_attempts must not be negative.")
        if lock_ttl_seconds <= 0:
            raise ValueError("Redis lock_ttl_seconds must be greater than zero.")
        self.url = url
        self.namespace = namespace
        self.timeout_seconds = timeout_seconds
        self.reconnect_attempts = reconnect_attempts
        self.lock_ttl_seconds = lock_ttl_seconds
        self._client = client
        self._external_client = client is not None
        self._connected = False
        self._subscribers: dict[str, list[Callable[[Any], None]]] = {}
        self._lock = RLock()

    def connect(self) -> None:
        """Create or validate the client with bounded immediate reconnect attempts."""
        with self._lock:
            if self._connected:
                return
            client = self._client or self._create_client()
            self._client = client
        self._execute(lambda active: active.ping(), "connect")
        with self._lock:
            self._connected = True

    def disconnect(self) -> None:
        """Close only a client created by this backend; external clients stay owned."""
        with self._lock:
            if not self._connected and self._client is None:
                return
            client = self._client
            self._connected = False
            if not self._external_client:
                self._client = None
        if client is not None and not self._external_client:
            try:
                client.close()
            except Exception as error:
                raise RedisBackendOperationError(
                    "Redis client close failed."
                ) from error

    close = disconnect

    def get(self, key: str) -> Any | None:
        """Return a JSON-compatible value stored under the namespaced key."""
        value = self._execute(lambda client: client.get(self._key(key)), "get")
        if value is None:
            return None
        raw = value.decode("utf-8") if isinstance(value, bytes) else value
        try:
            return json.loads(raw)
        except (TypeError, json.JSONDecodeError) as error:
            raise RedisBackendOperationError(
                "Redis returned invalid JSON data."
            ) from error

    def set(self, key: str, value: Any) -> None:
        """Store one JSON-compatible value using the configured namespace."""
        payload = self._encode(value)
        self._execute(lambda client: client.set(self._key(key), payload), "set")

    def delete(self, key: str) -> bool:
        """Delete a namespaced key and report whether it existed."""
        deleted = self._execute(lambda client: client.delete(self._key(key)), "delete")
        return bool(deleted)

    def publish(self, topic: str, value: Any) -> None:
        """Publish JSON data and notify local compatibility subscribers safely."""
        payload = self._encode(value)
        self._execute(
            lambda client: client.publish(self._topic(topic), payload), "publish"
        )
        with self._lock:
            handlers = tuple(self._subscribers.get(topic, ()))
        for handler in handlers:
            try:
                handler(value)
            except Exception:
                continue

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """Register an in-process callback using the established backend contract."""
        with self._lock:
            handlers = self._subscribers.setdefault(topic, [])
            if handler not in handlers:
                handlers.append(handler)

    def acquire_lock(self, name: str, owner: str) -> bool:
        """Acquire a namespaced Redis lock, retaining same-owner compatibility."""
        lock_key = self._lock_key(name)
        with self._lock:
            current = self._execute(lambda client: client.get(lock_key), "lock lookup")
            current_owner = self._decode_owner(current)
            if current_owner == owner:
                return True
            acquired = self._execute(
                lambda client: client.set(
                    lock_key, owner, nx=True, ex=self.lock_ttl_seconds
                ),
                "lock acquire",
            )
            return bool(acquired)

    def release_lock(self, name: str, owner: str) -> bool:
        """Release a lock only if its current value matches the supplied owner."""
        lock_key = self._lock_key(name)
        with self._lock:
            current = self._execute(lambda client: client.get(lock_key), "lock lookup")
            if self._decode_owner(current) != owner:
                return False
            deleted = self._execute(
                lambda client: client.delete(lock_key), "lock release"
            )
            return bool(deleted)

    def health(self) -> bool:
        """Return lifecycle state without creating an implicit network probe."""
        with self._lock:
            return self._connected

    def probe_health(self, *, timeout_seconds: float | None = None) -> bool:
        """Explicitly ping Redis through the existing bounded reconnect path.

        ``timeout_seconds`` is validated for a common checker interface. Redis
        client socket timeouts are configured at construction time, so callers
        should use :class:`BackendConfig` when a different client timeout is
        required.
        """
        if timeout_seconds is not None and timeout_seconds <= 0:
            raise ValueError("Health probe timeout_seconds must be greater than zero.")
        self.connect()
        return bool(self._execute(lambda client: client.ping(), "health probe"))

    async def aconnect(self) -> None:
        """Connect through a worker thread for async callers using sync clients."""
        await asyncio.to_thread(self.connect)

    async def adisconnect(self) -> None:
        """Disconnect through a worker thread for async callers."""
        await asyncio.to_thread(self.disconnect)

    async def aget(self, key: str) -> Any | None:
        """Read one value without blocking an async event loop."""
        return await asyncio.to_thread(self.get, key)

    async def aset(self, key: str, value: Any) -> None:
        """Store one value without blocking an async event loop."""
        await asyncio.to_thread(self.set, key, value)

    async def adelete(self, key: str) -> bool:
        """Delete one value without blocking an async event loop."""
        return await asyncio.to_thread(self.delete, key)

    def _execute(self, operation: Callable[[RedisClient], Any], name: str) -> Any:
        """Run an operation, reconnecting once per configured bounded retry budget."""
        for attempt in range(self.reconnect_attempts + 1):
            try:
                client = self._require_client()
                return operation(client)
            except RedisBackendUnavailableError:
                raise
            except Exception as error:
                if attempt >= self.reconnect_attempts:
                    message = (
                        f"Redis {name} operation failed after {attempt + 1} attempt(s)."
                    )
                    if name == "connect":
                        raise RedisBackendConnectionError(message) from error
                    raise RedisBackendOperationError(message) from error
                self._reconnect()
        raise AssertionError("Unreachable bounded Redis retry loop.")

    def _reconnect(self) -> None:
        """Reset connection state and validate the current or replacement client."""
        with self._lock:
            self._connected = False
            if not self._external_client:
                self._client = None
            client = self._client or self._create_client()
            self._client = client
        try:
            client.ping()
        except Exception as error:
            raise RedisBackendConnectionError("Redis reconnect failed.") from error
        with self._lock:
            self._connected = True

    def _require_client(self) -> RedisClient:
        with self._lock:
            client = self._client
        if client is None:
            self.connect()
            with self._lock:
                client = self._client
        if client is None:
            raise RedisBackendConnectionError("Redis client was not initialized.")
        return client

    def _create_client(self) -> RedisClient:
        """Import and configure redis-py lazily so it remains an optional extra."""
        try:
            redis_module = import_module("redis")
        except ModuleNotFoundError as error:
            raise RedisBackendUnavailableError(
                "Redis support requires the optional dependency: "
                "pip install tkai[redis]"
            ) from error
        redis_class = getattr(redis_module, "Redis", None)
        if redis_class is None:
            raise RedisBackendUnavailableError(
                "Installed redis dependency does not expose Redis client support."
            )
        return cast(
            RedisClient,
            redis_class.from_url(
                self.url,
                socket_connect_timeout=self.timeout_seconds,
                socket_timeout=self.timeout_seconds,
                decode_responses=False,
            ),
        )

    def _key(self, key: str) -> str:
        return f"{self.namespace}:value:{key}"

    def _topic(self, topic: str) -> str:
        return f"{self.namespace}:topic:{topic}"

    def _lock_key(self, name: str) -> str:
        return f"{self.namespace}:lock:{name}"

    @staticmethod
    def _encode(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError) as error:
            raise RedisBackendOperationError(
                "Redis backend values must be JSON-compatible."
            ) from error

    @staticmethod
    def _decode_owner(value: bytes | str | None) -> str | None:
        if value is None:
            return None
        return value.decode("utf-8") if isinstance(value, bytes) else value
