"""Thread-safe in-memory Marketplace registry for reference descriptors only."""

from __future__ import annotations

from threading import RLock

from .errors import PackageConflictError, PackageNotFoundError
from .models import PackageDescriptor, PackageKind


class MarketplaceRegistry:
    """Store immutable package descriptors without artifact, cache, or I/O state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._packages: dict[str, PackageDescriptor] = {}

    def register(self, package: PackageDescriptor) -> PackageDescriptor:
        """Register one descriptor or raise if its explicit id already exists."""
        with self._lock:
            if package.package_id in self._packages:
                raise PackageConflictError(package.package_id)
            self._packages[package.package_id] = package
            return package

    def unregister(self, package_id: str) -> PackageDescriptor:
        """Remove and return one descriptor without uninstalling anything."""
        with self._lock:
            try:
                return self._packages.pop(package_id)
            except KeyError as exc:
                raise PackageNotFoundError(package_id) from exc

    def get(self, package_id: str) -> PackageDescriptor:
        """Return one immutable descriptor from the local registry."""
        with self._lock:
            try:
                return self._packages[package_id]
            except KeyError as exc:
                raise PackageNotFoundError(package_id) from exc

    def list(self, kind: PackageKind | None = None) -> tuple[PackageDescriptor, ...]:
        """Return a stable immutable snapshot, optionally filtered by kind."""
        with self._lock:
            return tuple(
                package
                for _, package in sorted(self._packages.items())
                if kind is None or package.kind is kind
            )

    def exists(self, package_id: str) -> bool:
        """Return whether the explicit package identifier is registered."""
        with self._lock:
            return package_id in self._packages

    def snapshot(self) -> tuple[PackageDescriptor, ...]:
        """Return a stable read-only view of all local descriptors."""
        return self.list()

    def clear(self) -> None:
        """Idempotently remove local descriptor declarations."""
        with self._lock:
            self._packages.clear()
