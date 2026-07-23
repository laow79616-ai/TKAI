"""Configuration and construction helpers for optional distributed backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .backend import DistributedBackend, LocalBackend
from .redis import RedisBackend, RedisClient


@dataclass(frozen=True, slots=True)
class BackendConfig:
    """Immutable backend settings; the local backend remains the default."""

    kind: Literal["local", "redis"] = "local"
    url: str = "redis://localhost:6379/0"
    namespace: str = "tkai"
    timeout_seconds: float = 5.0
    reconnect_attempts: int = 1

    def __post_init__(self) -> None:
        """Reject malformed settings before any optional client is created."""
        if not self.url:
            raise ValueError("Backend URL must not be empty.")
        if not self.namespace:
            raise ValueError("Backend namespace must not be empty.")
        if self.timeout_seconds <= 0:
            raise ValueError("Backend timeout_seconds must be greater than zero.")
        if self.reconnect_attempts < 0:
            raise ValueError("Backend reconnect_attempts must not be negative.")


class BackendFactory:
    """Create explicit backend instances without changing coordinator defaults."""

    @staticmethod
    def create(
        config: BackendConfig | None = None, *, client: RedisClient | None = None
    ) -> DistributedBackend:
        """Create a local or Redis backend from immutable configuration."""
        settings = config or BackendConfig()
        if settings.kind == "local":
            return LocalBackend()
        return RedisBackend(
            url=settings.url,
            namespace=settings.namespace,
            timeout_seconds=settings.timeout_seconds,
            reconnect_attempts=settings.reconnect_attempts,
            client=client,
        )


def create_backend(
    config: BackendConfig | None = None, *, client: RedisClient | None = None
) -> DistributedBackend:
    """Create a backend through :class:`BackendFactory` for functional callers."""
    return BackendFactory.create(config, client=client)
