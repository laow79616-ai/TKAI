"""Offline coverage for the Marketplace Server Publisher Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from marketplace.publisher import Publisher
from server import ReferencePublisherService as ArchitecturePublisherService
from server.publisher import (
    PublisherCapability,
    PublisherClosedError,
    PublisherConflictError,
    PublisherDescriptor,
    PublisherEventType,
    PublisherFilter,
    PublisherId,
    PublisherLevel,
    PublisherMetadata,
    PublisherNotFoundError,
    PublisherOrganization,
    PublisherProfile,
    PublisherQuery,
    PublisherRecord,
    PublisherSort,
    PublisherStateError,
    PublisherStatus,
    ReferencePublisherService,
    ReferencePublisherStorage,
)
from server.registry import ReferenceRegistryService


def _record(
    identifier: str,
    *,
    name: str | None = None,
    level: PublisherLevel = PublisherLevel.COMMUNITY,
    organization: PublisherOrganization | None = None,
    capabilities: frozenset[PublisherCapability] = frozenset(),
) -> PublisherRecord:
    return PublisherRecord(
        PublisherId(identifier),
        PublisherDescriptor(
            profile=PublisherProfile(name or f"{identifier} publisher"),
            level=level,
            organization=organization,
            capabilities=capabilities,
        ),
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    values = {"scope": "reference"}
    metadata = PublisherMetadata(values)
    record = _record("publisher-1")
    values["scope"] = "changed"

    assert metadata.values["scope"] == "reference"
    with pytest.raises(TypeError):
        metadata.values["extra"] = "not allowed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        record.status = PublisherStatus.SUSPENDED  # type: ignore[misc]
    assert json.loads(json.dumps(record.to_dict()))["status"] == "active"


def test_create_update_and_duplicate_rejection_preserve_storage() -> None:
    service = ReferencePublisherService(ReferencePublisherStorage())
    original = service.create(_record("publisher-1", name="Original"))
    historical = service.snapshot()
    with pytest.raises(PublisherConflictError):
        service.create(_record("publisher-1", name="Duplicate"))
    updated = service.update(
        "publisher-1", PublisherDescriptor(PublisherProfile("Updated"))
    )

    assert original.descriptor.profile.name == "Original"
    assert historical.publishers == (original,)
    assert updated.descriptor.profile.name == "Updated"
    assert service.list() == (updated,)
    with pytest.raises(PublisherNotFoundError):
        service.get("missing")


def test_lifecycle_is_valid_idempotent_and_records_only_real_transitions() -> None:
    service = ReferencePublisherService()
    service.create(_record("publisher-1"))
    assert service.suspend("publisher-1").status is PublisherStatus.SUSPENDED
    assert service.suspend("publisher-1").status is PublisherStatus.SUSPENDED
    assert service.restore("publisher-1").status is PublisherStatus.ACTIVE
    assert service.deprecate("publisher-1").status is PublisherStatus.DEPRECATED
    assert service.restore("publisher-1").status is PublisherStatus.ACTIVE
    assert service.delete("publisher-1").status is PublisherStatus.DELETED
    assert service.delete("publisher-1").status is PublisherStatus.DELETED
    with pytest.raises(PublisherStateError):
        service.restore("publisher-1")

    assert tuple(event.event_type for event in service.events()) == (
        PublisherEventType.CREATED,
        PublisherEventType.SUSPENDED,
        PublisherEventType.RESTORED,
        PublisherEventType.DEPRECATED,
        PublisherEventType.RESTORED,
        PublisherEventType.DELETED,
    )
    assert tuple(event.sequence for event in service.events()) == tuple(
        range(1, len(service.events()) + 1)
    )


def test_capabilities_are_explicit_and_duplicate_or_missing_changes_fail() -> None:
    service = ReferencePublisherService()
    service.create(_record("publisher-1"))
    capability = PublisherCapability("publish_package", "Reference only")
    updated = service.add_capability("publisher-1", capability)
    with pytest.raises(PublisherConflictError):
        service.add_capability("publisher-1", capability)
    removed = service.remove_capability("publisher-1", capability.name)
    with pytest.raises(PublisherNotFoundError):
        service.remove_capability("publisher-1", capability.name)

    assert updated.descriptor.capabilities == frozenset((capability,))
    assert removed.descriptor.capabilities == frozenset()


def test_search_statistics_and_snapshot_have_stable_order_and_history() -> None:
    service = ReferencePublisherService()
    organization = PublisherOrganization("org-1", "Acme")
    service.create(
        _record(
            "b",
            name="Bravo",
            level=PublisherLevel.VERIFIED,
            organization=organization,
            capabilities=frozenset((PublisherCapability("manage_versions"),)),
        )
    )
    service.create(_record("a", name="Alpha", level=PublisherLevel.OFFICIAL))
    historical = service.snapshot()
    service.suspend("b")

    assert service.search(PublisherQuery(keyword="alpha")).publishers[
        0
    ].publisher_id == PublisherId("a")
    assert (
        service.search(
            PublisherQuery(publisher_filter=PublisherFilter(publisher_id="a"))
        ).total
        == 1
    )
    assert (
        service.search(
            PublisherQuery(publisher_filter=PublisherFilter(name="Alpha"))
        ).total
        == 1
    )
    assert (
        service.search(
            PublisherQuery(publisher_filter=PublisherFilter(organization="Acme"))
        ).total
        == 1
    )
    assert (
        service.search(
            PublisherQuery(
                publisher_filter=PublisherFilter(level=PublisherLevel.VERIFIED)
            )
        ).total
        == 1
    )
    assert (
        service.search(
            PublisherQuery(
                publisher_filter=PublisherFilter(status=PublisherStatus.SUSPENDED)
            )
        ).total
        == 1
    )
    assert (
        service.search(
            PublisherQuery(
                publisher_filter=PublisherFilter(capability="manage_versions")
            )
        ).total
        == 1
    )
    assert tuple(
        record.publisher_id
        for record in service.search(PublisherQuery(sort=PublisherSort.NAME)).publishers
    ) == (PublisherId("a"), PublisherId("b"))
    assert historical.statistics.active == 2
    assert service.statistics().suspended == 1
    assert service.statistics().organizations == 1
    assert (
        json.loads(json.dumps(historical.to_dict()))["statistics"]["total_publishers"]
        == 2
    )


def test_clear_failure_isolation_and_final_snapshot_after_idempotent_close() -> None:
    first = ReferencePublisherService()
    second = ReferencePublisherService()
    first.create(_record("publisher-1"))
    second.create(_record("publisher-2"))
    cleared = first.clear()
    snapshot_before_close = first.snapshot()
    first.close()
    first.close()

    assert len(cleared) == 1
    assert snapshot_before_close.publishers == ()
    assert first.snapshot().closed is True
    assert first.statistics().total_publishers == 0
    assert first.events()[-1].event_type is PublisherEventType.CLOSED
    assert second.get("publisher-2").status is PublisherStatus.ACTIVE
    with pytest.raises(PublisherClosedError):
        first.create(_record("publisher-3"))
    with pytest.raises(PublisherClosedError):
        first.clear()


def test_thread_safety_and_import_compatibility_remain_isolated() -> None:
    service = ReferencePublisherService()

    def create(index: int) -> None:
        service.create(_record(f"publisher-{index:02d}"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(create, range(32)))

    assert len(service.list()) == 32
    assert service.snapshot().statistics.total_publishers == 32
    assert ReferenceRegistryService().list() == ()
    assert isinstance(ArchitecturePublisherService(), ArchitecturePublisherService)
    assert Publisher.__module__ == "marketplace.publisher.models"
