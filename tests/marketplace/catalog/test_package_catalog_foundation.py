"""Offline Package Catalog Foundation regression tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from marketplace.models import PackageDependency, PackageVersion
from marketplace.package_catalog import (
    CompatibilityDescriptor,
    PackageCategory,
    PackageCompatibility,
    PackageDescriptor,
    PackageFilter,
    PackageIconDescriptor,
    PackageManifest,
    PackageMetadata,
    PackageQuery,
    PackageSort,
    PackageTag,
    ReferenceCatalogService,
)
from marketplace.package_catalog.errors import (
    CatalogPackageConflictError,
    CatalogPackageNotFoundError,
)


def _package(
    package_id: str,
    *,
    category: PackageCategory = PackageCategory.PLUGIN,
    publisher_id: str = "publisher",
    name: str = "Package",
    tag: str = "reference",
    version: PackageVersion | None = None,
) -> PackageDescriptor:
    return PackageDescriptor(
        PackageManifest(
            package_id,
            publisher_id,
            name,
            "Offline reference package",
            PackageVersion(1) if version is None else version,
            category,
            frozenset({PackageTag(tag)}),
            PackageCompatibility(runtime="1.3", sdk="2.0", studio="2.1"),
            (PackageDependency("base", required=False),),
            PackageMetadata("Reference", PackageIconDescriptor("package")),
        )
    )


def test_manifest_metadata_and_compatibility_are_immutable_and_json_safe() -> None:
    """Manifest descriptors defensively hold all documented catalog declarations."""
    descriptor = _package("plugin")
    manifest = descriptor.manifest
    assert manifest.to_dict()["compatibility"] == {
        "runtime": "1.3",
        "sdk": "2.0",
        "studio": "2.1",
        "enterprise": None,
        "cloud": None,
    }
    assert isinstance(manifest.compatibility, CompatibilityDescriptor)
    with pytest.raises(FrozenInstanceError):
        manifest.name = "Changed"


def test_reference_catalog_list_get_filter_search_sort_and_snapshot() -> None:
    """Catalog operations are deterministic, local, and independent of Registry."""
    service = ReferenceCatalogService()
    service.register(_package("tool", category=PackageCategory.TOOL, name="Zulu"))
    service.register(
        _package("plugin", publisher_id="other", name="Alpha", tag="featured")
    )

    assert service.get("tool").package_id == "tool"
    assert [
        item.package_id
        for item in service.catalog.filter(PackageFilter(tag=PackageTag("featured")))
    ] == ["plugin"]
    result = service.search(PackageQuery(keyword="alpha", sort=PackageSort.NAME))
    assert result.total == 1 and result.packages[0].package_id == "plugin"
    assert [item.package_id for item in service.catalog.sort(service.list())] == [
        "plugin",
        "tool",
    ]
    assert service.snapshot() == service.list()


def test_reference_catalog_registration_errors_and_cleanup_are_explicit() -> None:
    """Duplicate and missing local catalog entries remain isolated from packages."""
    service = ReferenceCatalogService()
    service.register(_package("package"))
    with pytest.raises(CatalogPackageConflictError):
        service.register(_package("package"))
    with pytest.raises(CatalogPackageNotFoundError):
        service.get("missing")
    service.close()
    service.close()
    assert service.snapshot() == ()


def test_reference_catalog_is_thread_safe_with_stable_snapshots() -> None:
    """Concurrent local registration and reads do not create global state or workers."""
    service = ReferenceCatalogService()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(lambda index: service.register(_package(str(index))), range(8))
        )
        snapshots = list(executor.map(lambda _index: service.snapshot(), range(8)))
    assert all(len(snapshot) == 8 for snapshot in snapshots)
    assert [item.package_id for item in service.snapshot()] == [
        str(index) for index in range(8)
    ]


def test_catalog_documentation_declares_reference_only_scope() -> None:
    """Documentation rules out download, installation, Registry, and resolver work."""
    document = (Path(__file__).parents[3] / "docs" / "PackageCatalog.md").read_text(
        encoding="utf-8"
    )
    assert "No network" in document
    assert "download" in document
    assert "installation" in document
    assert "resolver" in document
