"""Explicit local and Redis-backed service discovery with TTL-based cleanup."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import Event, RLock, Thread, current_thread
from types import MappingProxyType
from typing import Protocol

from .errors import ServiceInstanceNotFoundError
from .redis import RedisBackend


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class ServiceInstance:
    """Immutable service endpoint metadata with a UTC expiration timestamp."""

    service: str
    instance_id: str
    endpoint: str
    registered_at: datetime
    expires_at: datetime
    version: str | None = None
    region: str | None = None
    tags: frozenset[str] = frozenset()
    metadata: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        """Normalize metadata and timestamps without exposing mutable state."""
        if not self.service or not self.instance_id or not self.endpoint:
            raise ValueError("service, instance_id, and endpoint must not be empty.")
        for field_name in ("registered_at", "expires_at"):
            value = getattr(self, field_name)
            if value.tzinfo is None:
                raise ValueError(f"{field_name} must be timezone-aware.")
            object.__setattr__(self, field_name, value.astimezone(timezone.utc))
        if self.expires_at <= self.registered_at:
            raise ValueError("expires_at must be later than registered_at.")
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(
            self,
            "metadata",
            MappingProxyType(
                {str(key): str(value) for key, value in self.metadata.items()}
            ),
        )

    @classmethod
    def create(
        cls,
        service: str,
        instance_id: str,
        endpoint: str,
        *,
        ttl_seconds: float = 30.0,
        version: str | None = None,
        region: str | None = None,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> ServiceInstance:
        """Create one instance with deterministic injectable time for offline tests."""
        if ttl_seconds <= 0:
            raise ValueError("Service instance ttl_seconds must be greater than zero.")
        registered_at = now or _utc_now()
        return cls(
            service,
            instance_id,
            endpoint,
            registered_at,
            registered_at + timedelta(seconds=ttl_seconds),
            version,
            region,
            tags,
            metadata or {},
        )

    def renewed(
        self, ttl_seconds: float, *, now: datetime | None = None
    ) -> ServiceInstance:
        """Return a replacement instance with a refreshed expiration timestamp."""
        if ttl_seconds <= 0:
            raise ValueError("Service instance ttl_seconds must be greater than zero.")
        current = now or _utc_now()
        return ServiceInstance(
            self.service,
            self.instance_id,
            self.endpoint,
            self.registered_at,
            current + timedelta(seconds=ttl_seconds),
            self.version,
            self.region,
            self.tags,
            self.metadata,
        )

    def is_expired(self, *, now: datetime | None = None) -> bool:
        """Return whether this instance has reached its caller-selected TTL boundary."""
        return self.expires_at <= (now or _utc_now())

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-ready metadata without mutable implementation objects."""
        return {
            "service": self.service,
            "instance_id": self.instance_id,
            "endpoint": self.endpoint,
            "registered_at": self.registered_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "version": self.version,
            "region": self.region,
            "tags": sorted(self.tags),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> ServiceInstance:
        """Restore an instance from the JSON-compatible representation above."""
        tags = data.get("tags", [])
        metadata = data.get("metadata", {})
        if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
            raise ValueError("Service instance tags must be a list of strings.")
        if not isinstance(metadata, Mapping):
            raise ValueError("Service instance metadata must be a mapping.")
        return cls(
            str(data["service"]),
            str(data["instance_id"]),
            str(data["endpoint"]),
            datetime.fromisoformat(str(data["registered_at"])),
            datetime.fromisoformat(str(data["expires_at"])),
            _optional_string(data.get("version")),
            _optional_string(data.get("region")),
            frozenset(tags),
            {str(key): str(value) for key, value in metadata.items()},
        )


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) else None


class ServiceRegistry(Protocol):
    """Common explicit service-discovery contract for local and Redis registries."""

    def register(self, instance: ServiceInstance) -> ServiceInstance: ...
    def deregister(self, service: str, instance_id: str) -> bool: ...
    def renew(
        self,
        service: str,
        instance_id: str,
        *,
        ttl_seconds: float,
        now: datetime | None = None,
    ) -> ServiceInstance: ...
    def lookup(
        self,
        service: str,
        *,
        version: str | None = None,
        region: str | None = None,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> tuple[ServiceInstance, ...]: ...
    def list(self, *, now: datetime | None = None) -> tuple[ServiceInstance, ...]: ...
    def cleanup(self, *, now: datetime | None = None) -> int: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...


class LocalServiceRegistry:
    """Thread-safe in-memory registry with an explicit cleanup lifecycle."""

    def __init__(self, *, cleanup_interval_seconds: float = 30.0) -> None:
        """Create a stopped local registry that never performs network I/O."""
        if cleanup_interval_seconds <= 0:
            raise ValueError("cleanup_interval_seconds must be greater than zero.")
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._services: dict[str, dict[str, ServiceInstance]] = {}
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None

    def register(self, instance: ServiceInstance) -> ServiceInstance:
        """Register or replace one immutable local instance snapshot."""
        with self._lock:
            self._services.setdefault(instance.service, {})[
                instance.instance_id
            ] = instance
        return instance

    def deregister(self, service: str, instance_id: str) -> bool:
        """Remove an instance and report whether it existed."""
        with self._lock:
            instances = self._services.get(service)
            if instances is None or instance_id not in instances:
                return False
            del instances[instance_id]
            if not instances:
                del self._services[service]
            return True

    def renew(
        self,
        service: str,
        instance_id: str,
        *,
        ttl_seconds: float,
        now: datetime | None = None,
    ) -> ServiceInstance:
        """Refresh one registered instance or raise a clear missing-instance error."""
        with self._lock:
            try:
                current = self._services[service][instance_id]
            except KeyError as error:
                raise ServiceInstanceNotFoundError(
                    f"Service instance '{service}/{instance_id}' is not registered."
                ) from error
            updated = current.renewed(ttl_seconds, now=now)
            self._services[service][instance_id] = updated
            return updated

    def lookup(
        self,
        service: str,
        *,
        version: str | None = None,
        region: str | None = None,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> tuple[ServiceInstance, ...]:
        """Return stable unexpired service matches using optional metadata filters."""
        self.cleanup(now=now)
        with self._lock:
            instances = tuple(self._services.get(service, {}).values())
        return _filter_instances(instances, version, region, tags, metadata)

    def list(self, *, now: datetime | None = None) -> tuple[ServiceInstance, ...]:
        """Return all unexpired local instances in stable service/id order."""
        self.cleanup(now=now)
        with self._lock:
            instances = tuple(
                instance
                for service in sorted(self._services)
                for _, instance in sorted(self._services[service].items())
            )
        return instances

    def cleanup(self, *, now: datetime | None = None) -> int:
        """Remove expired entries and return the number purged."""
        current = now or _utc_now()
        removed = 0
        with self._lock:
            for service, instances in tuple(self._services.items()):
                for instance_id, instance in tuple(instances.items()):
                    if instance.is_expired(now=current):
                        del instances[instance_id]
                        removed += 1
                if not instances:
                    del self._services[service]
        return removed

    def snapshot(self, *, now: datetime | None = None) -> tuple[ServiceInstance, ...]:
        """Return a read-only alias for the stable local listing."""
        return self.list(now=now)

    def start(self) -> None:
        """Start one optional cleanup worker; repeated starts are idempotent."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._run_cleanup,
                name="tkai-service-registry-cleanup",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop and join only the registry-owned cleanup worker."""
        with self._lock:
            thread = self._thread
            self._thread = None
            self._stop_event.set()
        if thread is not None and thread is not current_thread():
            thread.join(timeout=self.cleanup_interval_seconds)

    close = stop

    def _run_cleanup(self) -> None:
        while not self._stop_event.wait(self.cleanup_interval_seconds):
            self.cleanup()


class RedisServiceRegistry:
    """Optional service registry stored through an explicit :class:`RedisBackend`.

    The registry uses a service-specific index and instance records. It is
    intentionally client-injectable and does not own or disconnect the supplied
    backend. Index writes are not a distributed transaction in this foundation.
    """

    def __init__(
        self,
        backend: RedisBackend,
        *,
        namespace: str = "services",
        cleanup_interval_seconds: float = 30.0,
    ) -> None:
        """Configure an explicit Redis registry without connecting the backend."""
        if not namespace:
            raise ValueError("Service registry namespace must not be empty.")
        if cleanup_interval_seconds <= 0:
            raise ValueError("cleanup_interval_seconds must be greater than zero.")
        self.backend = backend
        self.namespace = namespace
        self.cleanup_interval_seconds = cleanup_interval_seconds
        self._known_services: set[str] = set()
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None

    def register(self, instance: ServiceInstance) -> ServiceInstance:
        """Store an immutable instance record and add it to its service index."""
        with self._lock:
            self.backend.set(
                self._instance_key(instance.service, instance.instance_id),
                instance.to_dict(),
            )
            index = self._index(instance.service)
            index.add(instance.instance_id)
            self._save_index(instance.service, index)
            self._known_services.add(instance.service)
        return instance

    def deregister(self, service: str, instance_id: str) -> bool:
        """Remove an instance record and its index membership if present."""
        with self._lock:
            index = self._index(service)
            existed = instance_id in index
            if existed:
                index.remove(instance_id)
                self._save_index(service, index)
            self.backend.delete(self._instance_key(service, instance_id))
            if not index:
                self._known_services.discard(service)
            return existed

    def renew(
        self,
        service: str,
        instance_id: str,
        *,
        ttl_seconds: float,
        now: datetime | None = None,
    ) -> ServiceInstance:
        """Refresh a stored Redis instance or raise a clear missing-instance error."""
        with self._lock:
            instance = self._read_instance(service, instance_id)
            if instance is None:
                raise ServiceInstanceNotFoundError(
                    f"Service instance '{service}/{instance_id}' is not registered."
                )
            updated = instance.renewed(ttl_seconds, now=now)
            self.backend.set(
                self._instance_key(service, instance_id), updated.to_dict()
            )
            return updated

    def lookup(
        self,
        service: str,
        *,
        version: str | None = None,
        region: str | None = None,
        tags: frozenset[str] = frozenset(),
        metadata: Mapping[str, str] | None = None,
        now: datetime | None = None,
    ) -> tuple[ServiceInstance, ...]:
        """Return stable, unexpired Redis-backed matches and purge stale entries."""
        self.cleanup(now=now)
        with self._lock:
            instances = tuple(
                instance
                for instance_id in sorted(self._index(service))
                if (instance := self._read_instance(service, instance_id)) is not None
            )
        return _filter_instances(instances, version, region, tags, metadata)

    def list(self, *, now: datetime | None = None) -> tuple[ServiceInstance, ...]:
        """Return all known unexpired Redis records in stable service/id order."""
        self.cleanup(now=now)
        with self._lock:
            instances = tuple(
                instance
                for service in sorted(self._known_services)
                for instance_id in sorted(self._index(service))
                if (instance := self._read_instance(service, instance_id)) is not None
            )
        return instances

    def cleanup(self, *, now: datetime | None = None) -> int:
        """Purge locally known expired Redis records and return the removal count."""
        current = now or _utc_now()
        removed = 0
        with self._lock:
            for service in tuple(self._known_services):
                index = self._index(service)
                for instance_id in tuple(index):
                    instance = self._read_instance(service, instance_id)
                    if instance is None or instance.is_expired(now=current):
                        self.backend.delete(self._instance_key(service, instance_id))
                        index.discard(instance_id)
                        removed += 1
                self._save_index(service, index)
                if not index:
                    self._known_services.discard(service)
        return removed

    def snapshot(self, *, now: datetime | None = None) -> tuple[ServiceInstance, ...]:
        """Return a stable Redis listing without exposing index internals."""
        return self.list(now=now)

    def start(self) -> None:
        """Start periodic cleanup without taking ownership of the Redis backend."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._run_cleanup,
                name="tkai-redis-service-registry-cleanup",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop and join the registry worker without disconnecting RedisBackend."""
        with self._lock:
            thread = self._thread
            self._thread = None
            self._stop_event.set()
        if thread is not None and thread is not current_thread():
            thread.join(timeout=self.cleanup_interval_seconds)

    close = stop

    def _index(self, service: str) -> set[str]:
        stored = self.backend.get(self._index_key(service))
        if not isinstance(stored, list) or not all(
            isinstance(item, str) for item in stored
        ):
            return set()
        return set(stored)

    def _save_index(self, service: str, index: set[str]) -> None:
        self.backend.set(self._index_key(service), sorted(index))

    def _read_instance(self, service: str, instance_id: str) -> ServiceInstance | None:
        data = self.backend.get(self._instance_key(service, instance_id))
        if not isinstance(data, Mapping):
            return None
        return ServiceInstance.from_dict(data)

    def _index_key(self, service: str) -> str:
        return f"{self.namespace}:index:{service}"

    def _instance_key(self, service: str, instance_id: str) -> str:
        return f"{self.namespace}:instance:{service}:{instance_id}"

    def _run_cleanup(self) -> None:
        while not self._stop_event.wait(self.cleanup_interval_seconds):
            self.cleanup()


def _filter_instances(
    instances: tuple[ServiceInstance, ...],
    version: str | None,
    region: str | None,
    tags: frozenset[str],
    metadata: Mapping[str, str] | None,
) -> tuple[ServiceInstance, ...]:
    required_metadata = metadata or {}
    return tuple(
        instance
        for instance in sorted(
            instances, key=lambda item: (item.service, item.instance_id)
        )
        if (version is None or instance.version == version)
        and (region is None or instance.region == region)
        and tags.issubset(instance.tags)
        and all(
            instance.metadata.get(key) == value
            for key, value in required_metadata.items()
        )
    )
