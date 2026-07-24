"""Regression tests for the pure-memory Marketplace Server Registry domain."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from server.registry import (
    ReferenceRegistryService,
    ReferenceRegistryStorage,
    RegistryClosedError,
    RegistryConflictError,
    RegistryCoordinate,
    RegistryDescriptor,
    RegistryEntry,
    RegistryEventType,
    RegistryFilter,
    RegistryId,
    RegistryMetadata,
    RegistryQuery,
    RegistrySort,
    RegistryStateError,
    RegistryStatus,
)


def _entry(
    identifier: str, *, publisher: str = "acme", package: str | None = None
) -> RegistryEntry:
    package_name = package or f"package-{identifier}"
    return RegistryEntry(
        registry_id=RegistryId(identifier),
        descriptor=RegistryDescriptor(
            coordinate=RegistryCoordinate(publisher, package_name, "1.0.0"),
            title=f"{package_name} title",
            metadata=RegistryMetadata({"scope": "reference"}),
        ),
    )


def test_models_are_immutable_defensive_and_json_ready() -> None:
    values = {"scope": "reference"}
    entry = _entry("entry-1")
    metadata = RegistryMetadata(values)
    values["scope"] = "changed"

    assert entry.registry_id.value == "entry-1"
    assert metadata.values["scope"] == "reference"
    with pytest.raises(TypeError):
        metadata.values["extra"] = "not allowed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        entry.status = RegistryStatus.DEPRECATED  # type: ignore[misc]
    assert json.loads(json.dumps(entry.to_dict()))["status"] == "active"


def test_reference_storage_and_service_lifecycle_emit_stable_events() -> None:
    service = ReferenceRegistryService(ReferenceRegistryStorage())
    created = service.create(_entry("entry-1"))
    updated = service.update(created.registry_id, created.descriptor)
    deprecated = service.deprecate(created.registry_id)
    withdrawn = service.withdraw(created.registry_id)
    deleted = service.delete(created.registry_id)
    restored = service.restore(created.registry_id)
    snapshot = service.snapshot()

    assert updated.status is RegistryStatus.ACTIVE
    assert deprecated.status is RegistryStatus.DEPRECATED
    assert withdrawn.status is RegistryStatus.WITHDRAWN
    assert deleted.status is RegistryStatus.DELETED
    assert restored.status is RegistryStatus.ACTIVE
    assert snapshot.entries == (restored,)
    assert tuple(event.sequence for event in snapshot.events) == tuple(
        range(1, len(snapshot.events) + 1)
    )
    assert tuple(event.event_type for event in snapshot.events) == (
        RegistryEventType.CREATED,
        RegistryEventType.UPDATED,
        RegistryEventType.DEPRECATED,
        RegistryEventType.WITHDRAWN,
        RegistryEventType.DELETED,
        RegistryEventType.RESTORED,
        RegistryEventType.SNAPSHOT,
    )
    service.close()
    service.close()
    assert service.events()[-1].event_type is RegistryEventType.CLOSED
    with pytest.raises(RegistryClosedError):
        service.list()


def test_duplicate_and_invalid_state_failures_do_not_pollute_reference_storage() -> (
    None
):
    service = ReferenceRegistryService()
    original = service.create(_entry("entry-1", package="shared"))
    with pytest.raises(RegistryConflictError):
        service.create(_entry("entry-2", package="shared"))
    deleted = service.delete(original.registry_id)
    with pytest.raises(RegistryStateError):
        service.update(deleted.registry_id, deleted.descriptor)
    with pytest.raises(RegistryStateError):
        service.delete(deleted.registry_id)

    assert service.get(original.registry_id) == deleted
    assert service.statistics().entries == 1
    assert service.statistics().deleted == 1


def test_search_snapshot_statistics_and_clear_are_stable_and_immutable() -> None:
    service = ReferenceRegistryService()
    service.create(_entry("b", publisher="beta", package="tool"))
    service.create(_entry("a", publisher="alpha", package="workflow"))
    service.deprecate("b")

    result = service.search(
        RegistryQuery(
            keyword="alpha",
            registry_filter=RegistryFilter(status=RegistryStatus.ACTIVE),
            sort=RegistrySort.PUBLISHER,
        )
    )
    snapshot = service.snapshot()
    removed = service.clear()

    assert result.total == 1
    assert result.entries[0].registry_id == RegistryId("a")
    assert tuple(item.registry_id for item in snapshot.entries) == (
        RegistryId("a"),
        RegistryId("b"),
    )
    assert snapshot.statistics.active == 1
    assert snapshot.statistics.deprecated == 1
    assert isinstance(snapshot.entries, tuple)
    assert len(removed) == 2
    assert service.statistics().deleted == 2
    assert json.loads(json.dumps(snapshot.to_dict()))["statistics"]["entries"] == 2


def test_reference_service_is_thread_safe_and_instances_are_isolated() -> None:
    first = ReferenceRegistryService()
    second = ReferenceRegistryService()

    def create(index: int) -> None:
        first.create(_entry(f"entry-{index:02d}"))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(create, range(32)))

    assert len(first.list()) == 32
    assert first.snapshot().statistics.entries == 32
    assert second.list() == ()
