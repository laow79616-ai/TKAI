"""Thread-safe in-memory reference catalog without Registry or artifact behavior."""

from __future__ import annotations

from threading import RLock

from .catalog import MarketplaceCatalog
from .errors import CatalogPackageConflictError, CatalogPackageNotFoundError
from .models import PackageDescriptor, PackageQuery, PackageSearchResult


class ReferenceCatalogService:
    """Own local package declarations only; no package Registry is used or changed."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._packages: dict[str, PackageDescriptor] = {}
        self._catalog = MarketplaceCatalog(self)

    @property
    def catalog(self) -> MarketplaceCatalog:
        """Return the read-only local catalog view."""
        return self._catalog

    def register(self, package: PackageDescriptor) -> PackageDescriptor:
        """Register a descriptor in this isolated reference catalog only."""
        with self._lock:
            if package.package_id in self._packages:
                raise CatalogPackageConflictError(package.package_id)
            self._packages[package.package_id] = package
            return package

    def unregister(self, package_id: str) -> PackageDescriptor:
        """Remove one local descriptor without uninstalling or deleting artifacts."""
        with self._lock:
            try:
                return self._packages.pop(package_id)
            except KeyError as exc:
                raise CatalogPackageNotFoundError(package_id) from exc

    def get(self, package_id: str) -> PackageDescriptor:
        """Return one local immutable descriptor."""
        with self._lock:
            try:
                return self._packages[package_id]
            except KeyError as exc:
                raise CatalogPackageNotFoundError(package_id) from exc

    def list(self) -> tuple[PackageDescriptor, ...]:
        """Return local descriptors in stable package-id order."""
        with self._lock:
            return tuple(package for _, package in sorted(self._packages.items()))

    def search(self, query: PackageQuery | None = None) -> PackageSearchResult:
        """Search this local catalog without network or Registry delegation."""
        return self._catalog.search(query)

    def snapshot(self) -> tuple[PackageDescriptor, ...]:
        """Return a stable immutable reference catalog snapshot."""
        return self.list()

    def close(self) -> None:
        """Idempotently clear reference-only in-memory catalog descriptors."""
        with self._lock:
            self._packages.clear()
