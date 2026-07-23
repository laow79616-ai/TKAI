"""Configuration and construction helpers for optional distributed backends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .backend import DistributedBackend, LocalBackend
from .discovery import LocalServiceRegistry, RedisServiceRegistry, ServiceRegistry
from .failover import FailoverBackend, FailoverConfig, FailoverManager
from .health import BackendHealthChecker, HealthProbeConfig, ProbeableBackend
from .redis import RedisBackend, RedisClient


@dataclass(frozen=True, slots=True)
class BackendConfig:
    """Immutable backend settings; the local backend remains the default."""

    kind: Literal["local", "redis"] = "local"
    url: str = "redis://localhost:6379/0"
    namespace: str = "tkai"
    timeout_seconds: float = 5.0
    reconnect_attempts: int = 1
    health_probe_interval_seconds: float = 30.0
    health_probe_timeout_seconds: float = 5.0
    health_probe_retries: int = 1

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
        HealthProbeConfig(
            interval_seconds=self.health_probe_interval_seconds,
            timeout_seconds=self.health_probe_timeout_seconds,
            retries=self.health_probe_retries,
        )


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

    @staticmethod
    def create_health_checker(
        backend: ProbeableBackend, config: BackendConfig | None = None
    ) -> BackendHealthChecker:
        """Create an explicit checker without changing backend default behavior."""
        settings = config or BackendConfig()
        return BackendHealthChecker(
            backend,
            config=HealthProbeConfig(
                interval_seconds=settings.health_probe_interval_seconds,
                timeout_seconds=settings.health_probe_timeout_seconds,
                retries=settings.health_probe_retries,
            ),
        )

    @staticmethod
    def create_failover_manager(
        primary: FailoverBackend,
        secondary: FailoverBackend | None = None,
        *,
        config: FailoverConfig | None = None,
    ) -> FailoverManager:
        """Create an explicit failover manager with local memory as fallback."""
        return FailoverManager(primary, secondary, config=config)

    @staticmethod
    def create_service_registry(
        *,
        backend: DistributedBackend | None = None,
        failover_manager: FailoverManager | None = None,
        cleanup_interval_seconds: float = 30.0,
    ) -> ServiceRegistry:
        """Create an explicit registry for a supplied backend or current fallback.

        A manager is sampled only during construction; a later failover never
        silently migrates discovery records or changes this registry's backend.
        """
        selected = failover_manager.active_backend if failover_manager else backend
        if isinstance(selected, RedisBackend):
            return RedisServiceRegistry(
                selected, cleanup_interval_seconds=cleanup_interval_seconds
            )
        return LocalServiceRegistry(cleanup_interval_seconds=cleanup_interval_seconds)


def create_backend(
    config: BackendConfig | None = None, *, client: RedisClient | None = None
) -> DistributedBackend:
    """Create a backend through :class:`BackendFactory` for functional callers."""
    return BackendFactory.create(config, client=client)
