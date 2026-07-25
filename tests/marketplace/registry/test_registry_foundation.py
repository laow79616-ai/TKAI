"""Offline regression coverage for the separate Marketplace Registry Foundation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from marketplace.models import PackageDependency, PackageVersion
from marketplace.package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageMetadata,
    PackageTag,
    ReferenceCatalogService,
)
from marketplace.publication import (
    PublicationId,
    PublicationRequest,
    PublicationStatus,
    ReferencePublicationService,
)
from marketplace.publisher import Publisher, PublisherProfile
from marketplace.registry import MarketplaceRegistry
from marketplace.registry_foundation import (
    ReferenceRegistryCatalogProjector,
    ReferenceRegistryPublicationAdapter,
    ReferenceRegistryService,
    RegistryClosedError,
    RegistryConflictError,
    RegistryEntryId,
    RegistryEventType,
    RegistryFilter,
    RegistryMetadata,
    RegistryPublicationError,
    RegistryQuery,
    RegistrySort,
    RegistryStatus,
)


def _publisher() -> Publisher:
    return Publisher("publisher", PublisherProfile("Reference Publisher"))


def _manifest(
    package_id: str = "package",
    *,
    version: PackageVersion | None = None,
    category: PackageCategory = PackageCategory.PLUGIN,
    name: str = "Reference Package",
    tag: str = "reference",
) -> PackageManifest:
    return PackageManifest(
        package_id,
        "publisher",
        name,
        "Offline Registry Foundation package",
        PackageVersion(1) if version is None else version,
        category,
        frozenset({PackageTag(tag)}),
        PackageCompatibility(runtime="1.3", sdk="2.0"),
        (PackageDependency("base", required=False),),
        PackageMetadata("Reference package"),
    )


def _accepted_snapshot(
    publication_id: str = "publication", *, manifest: PackageManifest | None = None
):
    service = ReferencePublicationService(_publisher())
    request = PublicationRequest(
        PublicationId(publication_id),
        "publisher",
        _manifest() if manifest is None else manifest,
    )
    service.submit(request)
    service.validate(publication_id)
    return service.accept(publication_id)


def _entry(
    entry_id: str = "entry", *, package_id: str = "package", name: str = "Package"
):
    snapshot = _accepted_snapshot(entry_id, manifest=_manifest(package_id, name=name))
    return ReferenceRegistryPublicationAdapter(_publisher()).entry_from_snapshot(
        RegistryEntryId(entry_id), snapshot
    )


def test_models_are_immutable_json_safe_and_defensive() -> None:
    source = {"source": "test"}
    entry = ReferenceRegistryPublicationAdapter(_publisher()).entry_from_snapshot(
        RegistryEntryId("entry"), _accepted_snapshot(), RegistryMetadata(source)
    )
    source["source"] = "changed"
    assert entry.metadata.values == {"source": "test"}
    assert entry.to_dict()["status"] == "active"
    with pytest.raises(FrozenInstanceError):
        entry.status = RegistryStatus.WITHDRAWN
    with pytest.raises(TypeError):
        entry.metadata.values["source"] = "changed"


def test_explicit_accepted_publication_adapter_rejects_non_accepted_snapshots() -> None:
    snapshot = _accepted_snapshot()
    draft = type(snapshot)(snapshot.request, PublicationStatus.SUBMITTED)
    adapter = ReferenceRegistryPublicationAdapter(_publisher())
    with pytest.raises(RegistryPublicationError):
        adapter.entry_from_snapshot(RegistryEntryId("draft"), draft)
    assert (
        adapter.entry_from_snapshot(RegistryEntryId("accepted"), snapshot).status
        is RegistryStatus.ACTIVE
    )


def test_registration_duplicate_coordinate_and_lookup_are_explicit() -> None:
    service = ReferenceRegistryService()
    entry = _entry()
    service.register(entry)
    assert service.get("entry") == entry
    assert service.get_by_coordinate(entry.coordinate) == entry
    assert service.exists(RegistryEntryId("entry"))
    with pytest.raises(RegistryConflictError):
        service.register(entry)
    with pytest.raises(RegistryConflictError):
        service.register(_entry("other"))


def test_register_publication_search_filter_sort_index_and_statistics_are_stable() -> (
    None
):
    service = ReferenceRegistryService()
    adapter = ReferenceRegistryPublicationAdapter(_publisher())
    service.register_publication(
        RegistryEntryId("z"),
        _accepted_snapshot(
            "z",
            manifest=_manifest(
                "tool", category=PackageCategory.TOOL, name="Zulu", tag="tools"
            ),
        ),
        adapter,
    )
    service.register_publication(
        RegistryEntryId("a"),
        _accepted_snapshot(
            "a", manifest=_manifest("plugin", name="Alpha", tag="featured")
        ),
        adapter,
    )
    assert [entry.entry_id.value for entry in service.list()] == ["a", "z"]
    assert [
        entry.entry_id.value
        for entry in service.filter(RegistryFilter(tag=PackageTag("featured")))
    ] == ["a"]
    result = service.search(
        RegistryQuery(keyword="alpha", sort=RegistrySort.PACKAGE_ID)
    )
    assert [entry.entry_id.value for entry in result.entries] == ["a"]
    assert service.snapshot().index.categories["plugin"] == ("a",)
    assert service.statistics().total_entries == 2


def test_status_lifecycle_events_clear_and_close_are_idempotent() -> None:
    service = ReferenceRegistryService()
    service.register(_entry())
    assert service.withdraw("entry").status is RegistryStatus.WITHDRAWN
    assert service.withdraw("entry").status is RegistryStatus.WITHDRAWN
    assert service.deprecate("entry").status is RegistryStatus.DEPRECATED
    assert service.restore("entry").status is RegistryStatus.ACTIVE
    assert [event.event_type for event in service.events()] == [
        RegistryEventType.REGISTERED,
        RegistryEventType.WITHDRAWN,
        RegistryEventType.DEPRECATED,
        RegistryEventType.RESTORED,
    ]
    service.clear()
    service.clear()
    service.close()
    service.close()
    assert [event.event_type for event in service.events()][-2:] == [
        RegistryEventType.CLEARED,
        RegistryEventType.CLOSED,
    ]
    with pytest.raises(RegistryClosedError):
        service.list()


def test_projection_is_read_only_and_legacy_registry_remains_distinct() -> None:
    entry = _entry()
    projected = ReferenceRegistryCatalogProjector().project(entry)
    catalog = ReferenceCatalogService()
    assert projected.package_id == entry.package_manifest.package_id
    assert catalog.snapshot() == ()
    assert isinstance(MarketplaceRegistry(), MarketplaceRegistry)


def test_reference_service_is_thread_safe_and_has_no_global_state() -> None:
    service = ReferenceRegistryService()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.register(
                    _entry(str(index), package_id=str(index))
                ),
                range(8),
            )
        )
        snapshots = list(executor.map(lambda _index: service.snapshot(), range(8)))
    assert all(len(snapshot.entries) == 8 for snapshot in snapshots)
    assert ReferenceRegistryService().list() == ()


def test_registry_documentation_declares_reference_only_scope() -> None:
    document = (Path(__file__).parents[3] / "docs" / "Registry.md").read_text(
        encoding="utf-8"
    )
    for phrase in (
        "Reference Only",
        "Offline Only",
        "No network",
        "No package download",
        "No package installation",
        "No resolver",
    ):
        assert phrase in document
