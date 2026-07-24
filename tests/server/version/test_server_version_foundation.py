"""Offline coverage for the Marketplace Server Version Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from marketplace.package_catalog import CompatibilityDescriptor
from server import ReferenceVersionService as ArchitectureVersionService
from server.package import ReferencePackageService
from server.publisher import ReferencePublisherService
from server.registry import ReferenceRegistryService
from server.version import (
    ReferenceVersionService,
    ReferenceVersionStorage,
    VersionClosedError,
    VersionConflictError,
    VersionDescriptor,
    VersionEventType,
    VersionFilter,
    VersionId,
    VersionLabel,
    VersionManifest,
    VersionMetadata,
    VersionNotFoundError,
    VersionQuery,
    VersionRecord,
    VersionSort,
    VersionStateError,
    VersionStatus,
)


def _record(
    identifier: str,
    *,
    package: str = "reference-package",
    publisher: str = "acme",
    semantic_version: str = "1.0.0",
    label: VersionLabel = VersionLabel.STABLE,
) -> VersionRecord:
    return VersionRecord(
        VersionId(identifier),
        VersionManifest(
            VersionDescriptor(package, publisher, semantic_version, label),
        ),
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    values = {"scope": "reference"}
    metadata = VersionMetadata(values)
    record = _record("version-1")
    values["scope"] = "changed"

    assert metadata.values["scope"] == "reference"
    with pytest.raises(TypeError):
        metadata.values["extra"] = "not allowed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        record.status = VersionStatus.DEPRECATED  # type: ignore[misc]
    assert json.loads(json.dumps(record.to_dict()))["status"] == "active"


def test_create_update_duplicate_and_missing_failures_preserve_records() -> None:
    service = ReferenceVersionService(ReferenceVersionStorage())
    original = service.create(_record("version-1"))
    historical = service.snapshot()
    with pytest.raises(VersionConflictError):
        service.create(_record("version-1", semantic_version="2.0.0"))
    updated = service.update(
        "version-1",
        VersionManifest(
            VersionDescriptor("reference-package", "acme", "1.0.1"),
        ),
    )

    assert historical.versions == (original,)
    assert updated.manifest.descriptor.semantic_version == "1.0.1"
    assert service.list() == (updated,)
    with pytest.raises(VersionNotFoundError):
        service.get("missing")


def test_lifecycle_is_stable_and_events_use_deterministic_sequences() -> None:
    service = ReferenceVersionService()
    service.create(_record("version-1"))
    assert service.withdraw("version-1").status is VersionStatus.WITHDRAWN
    assert service.withdraw("version-1").status is VersionStatus.WITHDRAWN
    assert service.restore("version-1").status is VersionStatus.ACTIVE
    assert service.deprecate("version-1").status is VersionStatus.DEPRECATED
    assert service.restore("version-1").status is VersionStatus.ACTIVE
    assert service.delete("version-1").status is VersionStatus.DELETED
    assert service.delete("version-1").status is VersionStatus.DELETED
    with pytest.raises(VersionStateError):
        service.restore("version-1")

    assert tuple(event.event_type for event in service.events()) == (
        VersionEventType.CREATED,
        VersionEventType.WITHDRAWN,
        VersionEventType.RESTORED,
        VersionEventType.DEPRECATED,
        VersionEventType.RESTORED,
        VersionEventType.DELETED,
    )
    assert tuple(event.sequence for event in service.events()) == tuple(
        range(1, len(service.events()) + 1)
    )


def test_search_statistics_and_snapshot_order_are_deterministic() -> None:
    service = ReferenceVersionService()
    service.create(
        _record(
            "b",
            package="beta-package",
            publisher="beta",
            semantic_version="2.0.0-beta",
            label=VersionLabel.BETA,
        )
    )
    service.create(
        _record(
            "a",
            package="alpha-package",
            publisher="alpha",
            semantic_version="1.0.0",
            label=VersionLabel.STABLE,
        )
    )
    snapshot = service.snapshot()
    service.withdraw("b")

    assert service.search(VersionQuery(keyword="alpha")).total == 1
    assert (
        service.search(
            VersionQuery(version_filter=VersionFilter(package="beta-package"))
        ).total
        == 1
    )
    assert (
        service.search(
            VersionQuery(version_filter=VersionFilter(publisher="beta"))
        ).total
        == 1
    )
    assert (
        service.search(
            VersionQuery(version_filter=VersionFilter(semantic_version="2.0.0-beta"))
        ).total
        == 1
    )
    assert (
        service.search(
            VersionQuery(version_filter=VersionFilter(label=VersionLabel.BETA))
        ).total
        == 1
    )
    assert (
        service.search(
            VersionQuery(version_filter=VersionFilter(status=VersionStatus.WITHDRAWN))
        ).total
        == 1
    )
    assert tuple(
        record.version_id
        for record in service.search(VersionQuery(sort=VersionSort.PUBLISHER)).versions
    ) == (VersionId("a"), VersionId("b"))
    assert snapshot.statistics.active == 2
    assert service.statistics().withdrawn == 1
    assert service.statistics().stable == 1
    assert service.statistics().beta == 1
    assert json.loads(json.dumps(snapshot.to_dict()))["statistics"]["versions"] == 2


def test_clear_instance_isolation_and_close_preserve_final_snapshot() -> None:
    first = ReferenceVersionService()
    second = ReferenceVersionService()
    first.create(_record("version-1"))
    second.create(_record("version-2"))
    assert len(first.clear()) == 1
    first.close()
    first.close()

    assert first.snapshot().versions == ()
    assert first.snapshot().closed is True
    assert first.events()[-1].event_type is VersionEventType.CLOSED
    assert second.get("version-2").status is VersionStatus.ACTIVE
    with pytest.raises(VersionClosedError):
        first.create(_record("version-3"))
    with pytest.raises(VersionClosedError):
        first.clear()


def test_thread_safety_and_domain_imports_remain_isolated() -> None:
    service = ReferenceVersionService()

    def create(index: int) -> None:
        service.create(_record(f"version-{index:02d}"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(create, range(32)))

    assert len(service.list()) == 32
    assert service.snapshot().statistics.versions == 32
    assert ReferenceRegistryService().list() == ()
    assert ReferencePublisherService().list() == ()
    assert ReferencePackageService().list() == ()
    assert isinstance(ArchitectureVersionService(), ArchitectureVersionService)
    assert CompatibilityDescriptor.__module__ == "marketplace.package_catalog.models"
