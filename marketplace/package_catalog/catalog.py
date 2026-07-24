"""Pure local catalog views for immutable Package Catalog descriptors."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import (
    PackageDescriptor,
    PackageFilter,
    PackageQuery,
    PackageSearchResult,
    PackageSort,
)


class CatalogSource(Protocol):
    """Minimal source boundary implemented by the local reference catalog service."""

    def get(self, package_id: str) -> PackageDescriptor: ...
    def list(self) -> tuple[PackageDescriptor, ...]: ...


class MarketplaceCatalog:
    """Search, filter, sort, and snapshot a caller-provided local catalog source."""

    def __init__(self, source: CatalogSource) -> None:
        self._source = source

    def list(self) -> tuple[PackageDescriptor, ...]:
        """Return a stable snapshot of all local package descriptors."""
        return self._source.list()

    def get(self, package_id: str) -> PackageDescriptor:
        """Get one descriptor without registry or network access."""
        return self._source.get(package_id)

    def filter(self, package_filter: PackageFilter) -> tuple[PackageDescriptor, ...]:
        """Filter the local snapshot deterministically using declarative fields."""
        return tuple(
            package
            for package in self.list()
            if self._matches_filter(package, package_filter)
        )

    def sort(
        self,
        packages: Iterable[PackageDescriptor],
        field: PackageSort = PackageSort.NAME,
        *,
        descending: bool = False,
    ) -> tuple[PackageDescriptor, ...]:
        """Return a deterministic locally sorted tuple of catalog descriptors."""
        return tuple(
            sorted(
                packages,
                key=lambda package: self._sort_key(package, field),
                reverse=descending,
            )
        )

    def search(self, query: PackageQuery | None = None) -> PackageSearchResult:
        """Search local metadata only; keywords never invoke remote catalog lookup."""
        query = PackageQuery() if query is None else query
        packages = self.filter(query.package_filter)
        if query.keyword:
            keyword = query.keyword.casefold()
            packages = tuple(
                package
                for package in packages
                if keyword in self._search_text(package).casefold()
            )
        ordered = self.sort(packages, query.sort, descending=query.descending)
        return PackageSearchResult(ordered, len(ordered))

    def snapshot(self) -> tuple[PackageDescriptor, ...]:
        """Return a stable immutable local catalog snapshot."""
        return self.list()

    @staticmethod
    def _matches_filter(
        package: PackageDescriptor, package_filter: PackageFilter
    ) -> bool:
        manifest = package.manifest
        return (
            (
                package_filter.category is None
                or manifest.category is package_filter.category
            )
            and (
                package_filter.publisher_id is None
                or manifest.publisher_id == package_filter.publisher_id
            )
            and (package_filter.tag is None or package_filter.tag in manifest.tags)
            and (
                package_filter.version is None
                or manifest.version == package_filter.version
            )
        )

    @staticmethod
    def _search_text(package: PackageDescriptor) -> str:
        manifest = package.manifest
        return " ".join(
            (manifest.name, manifest.description, manifest.publisher_id)
            + tuple(tag.value for tag in manifest.tags)
        )

    @staticmethod
    def _sort_key(package: PackageDescriptor, field: PackageSort) -> tuple[object, ...]:
        manifest = package.manifest
        if field is PackageSort.PUBLISHER:
            return (manifest.publisher_id, manifest.name, manifest.package_id)
        if field is PackageSort.VERSION:
            version = manifest.version
            return (
                version.major,
                version.minor,
                version.patch,
                "" if version.prerelease is None else version.prerelease,
                manifest.package_id,
            )
        return (manifest.name, manifest.package_id)
