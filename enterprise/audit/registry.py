"""Explicit thread-safe Audit service registry and idempotent lifecycle helper."""

from __future__ import annotations

from threading import RLock

from .errors import AuditConflictError, AuditNotFoundError
from .service import AuditService


class AuditRegistry:
    def __init__(self) -> None:
        self._services: dict[str, AuditService] = {}
        self._lock = RLock()

    def register(self, name: str, service: AuditService) -> None:
        with self._lock:
            if name in self._services:
                raise AuditConflictError(f"Audit service {name!r} is duplicate.")
            self._services[name] = service

    def unregister(self, name: str) -> AuditService:
        with self._lock:
            try:
                return self._services.pop(name)
            except KeyError as exc:
                raise AuditNotFoundError(
                    f"Audit service {name!r} was not found."
                ) from exc

    def lookup(self, name: str) -> AuditService:
        with self._lock:
            try:
                return self._services[name]
            except KeyError as exc:
                raise AuditNotFoundError(
                    f"Audit service {name!r} was not found."
                ) from exc

    def list(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._services))


class AuditLifecycle:
    """Owns explicitly supplied services and supports idempotent close/shutdown."""

    def __init__(self, services: tuple[AuditService, ...] = ()) -> None:
        self._services = services
        self._closed = False
        self._lock = RLock()

    def initialize(self) -> None:
        """Mark explicit ownership initialized without starting threads."""

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            for service in self._services:
                service.close()
            self._closed = True

    shutdown = close
