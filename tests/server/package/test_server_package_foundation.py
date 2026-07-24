"""Offline coverage for the Marketplace Server Package Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from marketplace.catalog import PackageDescriptor as MarketplacePackageDescriptor
from server import ReferencePackageService as ArchitecturePackageService
from server.package import (
    PackageCategory,
    PackageClosedError,
    PackageConflictError,
    PackageDescriptor,
    PackageEventType,
    PackageFilter,
    PackageId,
    PackageManifest,
    PackageMetadata,
    PackageNotFoundError,
    PackageQuery,
    PackageRecord,
    PackageSort,
    PackageStateError,
    PackageStatus,
    PackageTag,
    PackageVersionRef,
    ReferencePackageService,
    ReferencePackageStorage,
)
from server.publisher import ReferencePublisherService
from server.registry import ReferenceRegistryService


def _record(
    identifier: str,
    *,
    publisher: str = "acme",
    name: str | None = None,
    category: PackageCategory = PackageCategory.PLUGIN,
    version: str = "1.0.0",
    tags: frozenset[PackageTag] = frozenset(),
) -> PackageRecord:
    package_name = name or f"{identifier}-package"
    return PackageRecord(
        PackageId(identifier),
        PackageManifest(
            PackageDescriptor(publisher, package_name, category, tags=tags),
            PackageVersionRef(version),
        ),
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    values = {"scope": "reference"}
    metadata = PackageMetadata(values)
    record = _record("package-1")
    values["scope"] = "changed"

    assert metadata.values["scope"] == "reference"
    with pytest.raises(TypeError):
        metadata.values["extra"] = "not allowed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        record.status = PackageStatus.DEPRECATED  # type: ignore[misc]
    assert json.loads(json.dumps(record.to_dict()))["status"] == "active"


def test_create_update_duplicate_and_missing_failures_preserve_records() -> None:
    service = ReferencePackageService(ReferencePackageStorage())
    original = service.create(_record("package-1", name="Original"))
    historical = service.snapshot()
    with pytest.raises(PackageConflictError):
        service.create(_record("package-1", name="Duplicate"))
    updated = service.update(
        "package-1",
        PackageManifest(
            PackageDescriptor("acme", "Updated", PackageCategory.PLUGIN),
            PackageVersionRef("1.0.1"),
        ),
    )

    assert historical.packages == (original,)
    assert updated.manifest.descriptor.name == "Updated"
    assert service.list() == (updated,)
    with pytest.raises(PackageNotFoundError):
        service.get("missing")


def test_lifecycle_is_stable_and_events_use_deterministic_sequences() -> None:
    service = ReferencePackageService()
    service.create(_record("package-1"))
    assert service.withdraw("package-1").status is PackageStatus.WITHDRAWN
    assert service.withdraw("package-1").status is PackageStatus.WITHDRAWN
    assert service.restore("package-1").status is PackageStatus.ACTIVE
    assert service.deprecate("package-1").status is PackageStatus.DEPRECATED
    assert service.restore("package-1").status is PackageStatus.ACTIVE
    assert service.delete("package-1").status is PackageStatus.DELETED
    assert service.delete("package-1").status is PackageStatus.DELETED
    with pytest.raises(PackageStateError):
        service.restore("package-1")

    assert tuple(event.event_type for event in service.events()) == (
        PackageEventType.CREATED,
        PackageEventType.WITHDRAWN,
        PackageEventType.RESTORED,
        PackageEventType.DEPRECATED,
        PackageEventType.RESTORED,
        PackageEventType.DELETED,
    )
    assert tuple(event.sequence for event in service.events()) == tuple(
        range(1, len(service.events()) + 1)
    )


def test_search_statistics_and_snapshot_order_are_deterministic() -> None:
    service = ReferencePackageService()
    service.create(
        _record(
            "b",
            publisher="beta",
            name="Bravo",
            category=PackageCategory.TOOL,
            version="2.0.0",
            tags=frozenset((PackageTag("utility"),)),
        )
    )
    service.create(
        _record(
            "a",
            publisher="alpha",
            name="Alpha",
            category=PackageCategory.WORKFLOW,
            tags=frozenset((PackageTag("flow"),)),
        )
    )
    snapshot = service.snapshot()
    service.withdraw("b")

    assert service.search(PackageQuery(keyword="alpha")).total == 1
    assert (
        service.search(
            PackageQuery(package_filter=PackageFilter(publisher="beta"))
        ).total
        == 1
    )
    assert (
        service.search(
            PackageQuery(package_filter=PackageFilter(category=PackageCategory.TOOL))
        ).total
        == 1
    )
    assert (
        service.search(PackageQuery(package_filter=PackageFilter(tag="utility"))).total
        == 1
    )
    assert (
        service.search(
            PackageQuery(package_filter=PackageFilter(version="2.0.0"))
        ).total
        == 1
    )
    assert (
        service.search(
            PackageQuery(package_filter=PackageFilter(status=PackageStatus.WITHDRAWN))
        ).total
        == 1
    )
    assert tuple(
        record.package_id
        for record in service.search(PackageQuery(sort=PackageSort.PUBLISHER)).packages
    ) == (PackageId("a"), PackageId("b"))
    assert snapshot.statistics.active == 2
    assert service.statistics().withdrawn == 1
    assert service.statistics().categories == 2
    assert service.statistics().versions == 2
    assert service.statistics().tags == 2
    assert json.loads(json.dumps(snapshot.to_dict()))["statistics"]["packages"] == 2


def test_clear_instance_isolation_and_close_preserve_final_snapshot() -> None:
    first = ReferencePackageService()
    second = ReferencePackageService()
    first.create(_record("package-1"))
    second.create(_record("package-2"))
    assert len(first.clear()) == 1
    first.close()
    first.close()

    assert first.snapshot().packages == ()
    assert first.snapshot().closed is True
    assert first.events()[-1].event_type is PackageEventType.CLOSED
    assert second.get("package-2").status is PackageStatus.ACTIVE
    with pytest.raises(PackageClosedError):
        first.create(_record("package-3"))
    with pytest.raises(PackageClosedError):
        first.clear()


def test_thread_safety_and_domain_imports_remain_isolated() -> None:
    service = ReferencePackageService()

    def create(index: int) -> None:
        service.create(_record(f"package-{index:02d}"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(create, range(32)))

    assert len(service.list()) == 32
    assert service.snapshot().statistics.packages == 32
    assert ReferenceRegistryService().list() == ()
    assert ReferencePublisherService().list() == ()
    assert isinstance(ArchitecturePackageService(), ArchitecturePackageService)
    assert MarketplacePackageDescriptor.__module__ == "marketplace.models"
