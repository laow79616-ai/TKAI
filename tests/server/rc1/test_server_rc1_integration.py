"""Offline RC-1 integration validation for Marketplace Server V6 foundations."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from server.health import (
    HealthCheck,
    HealthCheckId,
    HealthClosedError,
    HealthNotFoundError,
    HealthResult,
    HealthStatus,
    ReferenceHealthService,
    ReferenceHealthStorage,
)
from server.package import (
    PackageCategory,
    PackageClosedError,
    PackageDescriptor,
    PackageId,
    PackageManifest,
    PackageRecord,
    PackageVersionRef,
    ReferencePackageService,
    ReferencePackageStorage,
)
from server.publisher import (
    PublisherClosedError,
    PublisherDescriptor,
    PublisherId,
    PublisherProfile,
    PublisherRecord,
    ReferencePublisherService,
    ReferencePublisherStorage,
)
from server.registry import (
    ReferenceRegistryService,
    ReferenceRegistryStorage,
    RegistryClosedError,
    RegistryConflictError,
    RegistryCoordinate,
    RegistryDescriptor,
    RegistryEntry,
    RegistryId,
)
from server.search import (
    ReferenceSearchService,
    ReferenceSearchStorage,
    SearchClosedError,
    SearchEntry,
    SearchQuery,
    SearchTarget,
)
from server.statistics import (
    ReferenceStatisticsService,
    ReferenceStatisticsStorage,
    StatisticsClosedError,
    StatisticsConflictError,
    StatisticsMetric,
    StatisticsMetricType,
    StatisticsRecord,
    StatisticsSource,
    StatisticsSourceType,
    StatisticsValue,
)
from server.version import (
    ReferenceVersionService,
    ReferenceVersionStorage,
    VersionClosedError,
    VersionDescriptor,
    VersionId,
    VersionManifest,
    VersionRecord,
)

ROOT = Path(__file__).resolve().parents[3]


def _registry(identifier: str = "registry") -> RegistryEntry:
    return RegistryEntry(
        RegistryId(identifier),
        RegistryDescriptor(RegistryCoordinate("publisher", "package", "1.0.0")),
    )


def _publisher(identifier: str = "publisher") -> PublisherRecord:
    return PublisherRecord(
        PublisherId(identifier), PublisherDescriptor(PublisherProfile(identifier))
    )


def _package(identifier: str = "package") -> PackageRecord:
    return PackageRecord(
        PackageId(identifier),
        PackageManifest(
            PackageDescriptor("publisher", identifier, PackageCategory.PLUGIN),
            PackageVersionRef("1.0.0"),
        ),
    )


def _version(identifier: str = "version") -> VersionRecord:
    return VersionRecord(
        VersionId(identifier),
        VersionManifest(VersionDescriptor("package", "publisher", "1.0.0")),
    )


def _services() -> tuple[
    ReferenceRegistryService,
    ReferencePublisherService,
    ReferencePackageService,
    ReferenceVersionService,
    ReferenceSearchService,
    ReferenceStatisticsService,
    ReferenceHealthService,
]:
    return (
        ReferenceRegistryService(ReferenceRegistryStorage()),
        ReferencePublisherService(ReferencePublisherStorage()),
        ReferencePackageService(ReferencePackageStorage()),
        ReferenceVersionService(ReferenceVersionStorage()),
        ReferenceSearchService(ReferenceSearchStorage()),
        ReferenceStatisticsService(ReferenceStatisticsStorage()),
        ReferenceHealthService(ReferenceHealthStorage()),
    )


def test_explicit_foundation_chain_supports_all_rc1_scenarios() -> None:
    registry, publisher, package, version, search, statistics, health = _services()
    registry.create(_registry())
    publisher.create(_publisher())
    package.create(_package())
    version.create(_version())
    search_entry = SearchEntry("package", SearchTarget.PACKAGE, "package")
    search = ReferenceSearchService(ReferenceSearchStorage((search_entry,)))
    assert search.search(SearchQuery("package")).total == 1

    for source_id, source_type in (
        ("registry", StatisticsSourceType.REGISTRY),
        ("publisher", StatisticsSourceType.PUBLISHER),
        ("package", StatisticsSourceType.PACKAGE),
        ("version", StatisticsSourceType.VERSION),
    ):
        statistics.register_source(StatisticsSource(source_id, source_type, source_id))
        statistics.record(
            StatisticsRecord(
                f"{source_id}-record",
                source_id,
                StatisticsMetric("items", StatisticsMetricType.COUNTER),
                StatisticsValue(1),
            )
        )
        health.register_check(HealthCheck(source_id))
        health.update_result(
            HealthResult(HealthCheckId(source_id), HealthStatus.HEALTHY)
        )

    assert registry.statistics().entries == publisher.statistics().total_publishers == 1
    assert package.statistics().packages == version.statistics().versions == 1
    assert statistics.counters().total_records == 4
    assert health.statistics().healthy == 4


def test_lifecycle_snapshots_events_and_close_semantics_are_consistent() -> None:
    registry, publisher, package, version, search, statistics, health = _services()
    registry.create(_registry())
    publisher.create(_publisher())
    package.create(_package())
    version.create(_version())
    search = ReferenceSearchService(
        ReferenceSearchStorage((SearchEntry("entry", SearchTarget.PACKAGE, "entry"),))
    )
    search.search()
    statistics.register_source(
        StatisticsSource("statistics", StatisticsSourceType.CUSTOM, "statistics")
    )
    statistics.record(
        StatisticsRecord(
            "record",
            "statistics",
            StatisticsMetric("items", StatisticsMetricType.COUNTER),
            StatisticsValue(1),
        )
    )
    health.register_check(HealthCheck("health"))

    before = tuple(
        service.snapshot()
        for service in (
            registry,
            publisher,
            package,
            version,
            search,
            statistics,
            health,
        )
    )
    for service in (registry, publisher, package, version, search, statistics, health):
        service.close()
        service.close()
    after = tuple(
        service.snapshot()
        for service in (
            registry,
            publisher,
            package,
            version,
            search,
            statistics,
            health,
        )
    )

    assert all(
        json.loads(json.dumps(snapshot.to_dict())) for snapshot in before + after
    )
    assert all(snapshot.closed for snapshot in after)
    assert all(
        sum(event.event_type.value == "closed" for event in service.events()) == 1
        for service in (
            registry,
            publisher,
            package,
            version,
            search,
            statistics,
            health,
        )
    )
    assert registry.statistics().entries == 1
    assert publisher.statistics().total_publishers == 1
    assert package.statistics().packages == 1
    assert version.statistics().versions == 1
    assert search.statistics().targets == 1
    assert statistics.counters().total_records == 1
    assert health.statistics().total_checks == 1
    with pytest.raises(RegistryClosedError):
        registry.create(_registry("other"))
    with pytest.raises(PublisherClosedError):
        publisher.create(_publisher("other"))
    with pytest.raises(PackageClosedError):
        package.create(_package("other"))
    with pytest.raises(VersionClosedError):
        version.create(_version("other"))
    with pytest.raises(SearchClosedError):
        search.search()
    with pytest.raises(StatisticsClosedError):
        statistics.record(
            StatisticsRecord(
                "other",
                "statistics",
                StatisticsMetric("items", StatisticsMetricType.COUNTER),
                StatisticsValue(1),
            )
        )
    with pytest.raises(HealthClosedError):
        health.register_check(HealthCheck("other"))


def test_failures_do_not_cross_domain_or_pollute_existing_state() -> None:
    registry, publisher, package, version, search, statistics, health = _services()
    registry.create(_registry())
    publisher.create(_publisher())
    package.create(_package())
    version.create(_version())
    statistics.register_source(
        StatisticsSource("source", StatisticsSourceType.CUSTOM, "source")
    )
    statistics.record(
        StatisticsRecord(
            "record",
            "source",
            StatisticsMetric("items", StatisticsMetricType.COUNTER),
            StatisticsValue(1),
        )
    )
    with pytest.raises(RegistryConflictError):
        registry.create(_registry("other"))
    with pytest.raises(StatisticsConflictError):
        statistics.record(
            StatisticsRecord(
                "record",
                "source",
                StatisticsMetric("items", StatisticsMetricType.COUNTER),
                StatisticsValue(2),
            )
        )
    with pytest.raises(HealthNotFoundError):
        health.update_result(
            HealthResult(HealthCheckId("missing"), HealthStatus.UNHEALTHY)
        )

    assert publisher.statistics().total_publishers == package.statistics().packages == 1
    assert version.statistics().versions == 1
    assert statistics.counters().total_records == 1
    assert search.snapshot().results == ()
    assert health.snapshot().checks == ()


def test_instances_thread_safety_compatibility_imports_and_package_docs() -> None:
    first = ReferenceHealthService()
    second = ReferenceHealthService()

    def register(index: int) -> str:
        identifier = f"health-{index:02d}"
        first.register_check(HealthCheck(identifier))
        first.update_result(
            HealthResult(HealthCheckId(identifier), HealthStatus.HEALTHY)
        )
        return identifier

    with ThreadPoolExecutor(max_workers=8) as executor:
        assert len(set(executor.map(register, range(32)))) == 32
    first.close()
    assert first.statistics().healthy == 32
    assert second.snapshot().checks == ()

    import cloud  # noqa: F401
    import enterprise  # noqa: F401
    import marketplace  # noqa: F401
    import studio  # noqa: F401
    import tkai  # noqa: F401

    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    package_config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for name in (
        "Architecture.md",
        "RegistryFoundation.md",
        "PublisherFoundation.md",
        "PackageFoundation.md",
        "VersionFoundation.md",
        "SearchFoundation.md",
        "StatisticsFoundation.md",
        "HealthFoundation.md",
    ):
        assert name in manifest and name in package_config
