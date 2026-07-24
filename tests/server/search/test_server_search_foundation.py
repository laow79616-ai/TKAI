"""Offline coverage for the Marketplace Server Search Foundation."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from server import ReferenceSearchService as ArchitectureSearchService
from server.package import ReferencePackageService
from server.publisher import ReferencePublisherService
from server.registry import ReferenceRegistryService
from server.search import (
    ReferenceSearchService,
    ReferenceSearchStorage,
    SearchClosedError,
    SearchEntry,
    SearchEventType,
    SearchFilter,
    SearchPage,
    SearchQuery,
    SearchSort,
    SearchTarget,
)
from server.version import ReferenceVersionService


def _entry(
    identifier: str,
    *,
    target: SearchTarget = SearchTarget.PACKAGE,
    name: str | None = None,
    publisher: str | None = "acme",
    package: str | None = "reference-package",
    category: str | None = "plugin",
    tags: frozenset[str] = frozenset(),
    version: str | None = "1.0.0",
    status: str | None = "active",
    keywords: tuple[str, ...] = (),
) -> SearchEntry:
    return SearchEntry(
        identifier=identifier,
        target=target,
        name=name or f"{identifier} name",
        publisher=publisher,
        package=package,
        category=category,
        tags=tags,
        version=version,
        status=status,
        keywords=keywords,
        metadata={"scope": "reference"},
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    values = {"scope": "reference"}
    entry = SearchEntry("entry-1", SearchTarget.PACKAGE, "Example", metadata=values)
    values["scope"] = "changed"

    assert entry.metadata["scope"] == "reference"
    with pytest.raises(TypeError):
        entry.metadata["extra"] = "not allowed"  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        entry.name = "changed"  # type: ignore[misc]
    assert json.loads(json.dumps(entry.to_dict()))["target"] == "package"


def test_search_filtering_sorting_paging_and_snapshot_are_deterministic() -> None:
    storage = ReferenceSearchStorage(
        (
            _entry(
                "b",
                target=SearchTarget.VERSION,
                name="Bravo",
                publisher="beta",
                package="beta-package",
                category="tool",
                tags=frozenset(("utility",)),
                version="2.0.0",
                keywords=("beta",),
            ),
            _entry(
                "a",
                target=SearchTarget.PUBLISHER,
                name="Alpha",
                publisher="alpha",
                package=None,
                category=None,
                tags=frozenset(("official",)),
                version=None,
                keywords=("alpha",),
            ),
        )
    )
    service = ReferenceSearchService(storage)

    result = service.search(SearchQuery(keyword="alpha", sort=SearchSort.NAME))
    assert result.entries[0].identifier == "a"
    assert (
        service.search(
            SearchQuery(search_filter=SearchFilter(target=SearchTarget.VERSION))
        ).total
        == 1
    )
    assert (
        service.search(SearchQuery(search_filter=SearchFilter(publisher="beta"))).total
        == 1
    )
    assert (
        service.search(
            SearchQuery(search_filter=SearchFilter(package="beta-package"))
        ).total
        == 1
    )
    assert (
        service.search(SearchQuery(search_filter=SearchFilter(category="tool"))).total
        == 1
    )
    assert (
        service.search(SearchQuery(search_filter=SearchFilter(tag="utility"))).total
        == 1
    )
    assert (
        service.search(SearchQuery(search_filter=SearchFilter(version="2.0.0"))).total
        == 1
    )
    assert (
        service.search(SearchQuery(search_filter=SearchFilter(status="active"))).total
        == 2
    )
    page = service.search(
        SearchQuery(sort=SearchSort.IDENTIFIER, page=SearchPage(limit=1))
    )
    snapshot = service.snapshot()

    assert page.total == 2 and page.entries[0].identifier == "a"
    assert snapshot.results == page.entries
    assert snapshot.statistics.queries == 9
    assert json.loads(json.dumps(snapshot.to_dict()))["closed"] is False


def test_suggestions_statistics_and_events_are_stable() -> None:
    service = ReferenceSearchService(
        ReferenceSearchStorage(
            (_entry("a", name="Alpha", keywords=("assistant",)),),
        )
    )
    assert service.suggest("a") == ("Alpha", "a", "assistant")
    service.search()

    assert service.statistics().suggestions == 1
    assert service.statistics().queries == 1
    assert service.statistics().results == 1
    assert tuple(event.event_type for event in service.snapshot().events) == (
        SearchEventType.SUGGESTED,
        SearchEventType.SEARCHED,
    )
    assert tuple(event.sequence for event in service.snapshot().events) == (1, 2)


def test_clear_failure_isolation_instance_isolation_and_close_semantics() -> None:
    first = ReferenceSearchService(ReferenceSearchStorage((_entry("a"),)))
    second = ReferenceSearchService(ReferenceSearchStorage((_entry("b"),)))
    first.search()
    assert len(first.clear()) == 1
    first.close()
    first.close()

    assert first.snapshot().results == ()
    assert first.snapshot().closed is True
    assert first.snapshot().events[-1].event_type is SearchEventType.CLOSED
    assert second.search().entries[0].identifier == "b"
    with pytest.raises(SearchClosedError):
        first.search()
    with pytest.raises(SearchClosedError):
        first.clear()


def test_thread_safety_is_bounded_and_other_domains_remain_isolated() -> None:
    entries = tuple(_entry(f"entry-{index:02d}") for index in range(32))
    service = ReferenceSearchService(ReferenceSearchStorage(entries))

    def search(_: int) -> int:
        return service.search(SearchQuery(keyword="entry")).total

    with ThreadPoolExecutor(max_workers=8) as executor:
        assert tuple(executor.map(search, range(32))) == (32,) * 32

    assert service.statistics().queries == 32
    assert ReferenceRegistryService().list() == ()
    assert ReferencePublisherService().list() == ()
    assert ReferencePackageService().list() == ()
    assert ReferenceVersionService().list() == ()
    assert isinstance(ArchitectureSearchService(), ArchitectureSearchService)
