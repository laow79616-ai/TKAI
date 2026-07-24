"""Cross-domain architecture contracts for Marketplace Server V6 foundations."""

from __future__ import annotations

import ast
import importlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from server.health import (
    HealthCheck,
    HealthCheckId,
    HealthResult,
    HealthStatus,
    ReferenceHealthService,
)
from server.package import (
    PackageCategory,
    PackageDescriptor,
    PackageId,
    PackageManifest,
    PackageRecord,
    PackageVersionRef,
    ReferencePackageService,
)
from server.publisher import (
    PublisherDescriptor,
    PublisherId,
    PublisherProfile,
    PublisherRecord,
    ReferencePublisherService,
)
from server.registry import (
    ReferenceRegistryService,
    RegistryCoordinate,
    RegistryDescriptor,
    RegistryEntry,
    RegistryId,
)
from server.search import (
    ReferenceSearchService,
    ReferenceSearchStorage,
    SearchEntry,
    SearchQuery,
    SearchTarget,
)
from server.statistics import (
    ReferenceStatisticsService,
    StatisticsMetric,
    StatisticsMetricType,
    StatisticsRecord,
    StatisticsSource,
    StatisticsSourceType,
    StatisticsValue,
)
from server.version import (
    ReferenceVersionService,
    VersionDescriptor,
    VersionId,
    VersionManifest,
    VersionRecord,
)

DOMAIN_MODULES = (
    "server.registry",
    "server.publisher",
    "server.package",
    "server.version",
    "server.search",
    "server.statistics",
    "server.health",
)
DOMAIN_NAMES = {name.rsplit(".", 1)[-1] for name in DOMAIN_MODULES}
ROOT = Path(__file__).resolve().parents[3]


def _registry_entry(identifier: str = "registry") -> RegistryEntry:
    return RegistryEntry(
        RegistryId(identifier),
        RegistryDescriptor(RegistryCoordinate("acme", identifier, "1.0.0")),
    )


def _publisher_record(identifier: str = "publisher") -> PublisherRecord:
    return PublisherRecord(
        PublisherId(identifier), PublisherDescriptor(PublisherProfile(identifier))
    )


def _package_record(identifier: str = "package") -> PackageRecord:
    return PackageRecord(
        PackageId(identifier),
        PackageManifest(
            PackageDescriptor("acme", identifier, PackageCategory.PLUGIN),
            PackageVersionRef("1.0.0"),
        ),
    )


def _version_record(identifier: str = "version") -> VersionRecord:
    return VersionRecord(
        VersionId(identifier),
        VersionManifest(VersionDescriptor("package", "acme", "1.0.0")),
    )


def _statistics_service() -> ReferenceStatisticsService:
    service = ReferenceStatisticsService()
    service.register_source(
        StatisticsSource("statistics", StatisticsSourceType.CUSTOM, "Statistics")
    )
    service.record(
        StatisticsRecord(
            "record",
            "statistics",
            StatisticsMetric("items", StatisticsMetricType.COUNTER),
            StatisticsValue(1),
        )
    )
    return service


@pytest.mark.parametrize("module_name", DOMAIN_MODULES)
def test_public_domain_imports_are_explicit_and_stable(module_name: str) -> None:
    module = importlib.import_module(module_name)
    exported = module.__all__

    assert isinstance(exported, tuple)
    assert exported == tuple(sorted(exported))
    assert all(not name.startswith("_") for name in exported)
    assert all(
        "lock" not in name.lower() and "container" not in name.lower()
        for name in exported
    )
    assert all(hasattr(module, name) for name in exported)


def test_domain_implementations_have_no_cross_domain_or_forbidden_imports() -> None:
    forbidden = {"requests", "httpx", "redis", "sqlite3", "socket", "subprocess"}
    for path in ROOT.glob("server/**/*.py"):
        if path.name == "__init__.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Import, ast.ImportFrom)):
                continue
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            for name in names:
                root = name.split(".", 1)[0]
                assert root not in forbidden
                if name.startswith("server."):
                    domain = name.split(".")[1]
                    current = (
                        path.parent.name
                        if path.parent != ROOT / "server"
                        else path.stem
                    )
                    assert domain == current or current not in DOMAIN_NAMES


def test_snapshots_are_historical_json_safe_and_finally_readable() -> None:
    registry = ReferenceRegistryService()
    publisher = ReferencePublisherService()
    package = ReferencePackageService()
    version = ReferenceVersionService()
    search = ReferenceSearchService(
        ReferenceSearchStorage((SearchEntry("search", SearchTarget.PACKAGE, "Search"),))
    )
    statistics = _statistics_service()
    health = ReferenceHealthService()
    health.register_check(HealthCheck("health"))
    health.update_result(HealthResult(HealthCheckId("health"), HealthStatus.HEALTHY))

    registry.create(_registry_entry())
    publisher.create(_publisher_record())
    package.create(_package_record())
    version.create(_version_record())
    search.search(SearchQuery())
    snapshots = (
        registry.snapshot(),
        publisher.snapshot(),
        package.snapshot(),
        version.snapshot(),
        search.snapshot(),
        statistics.snapshot(),
        health.snapshot(),
    )
    registry.clear()
    publisher.clear()
    package.clear()
    version.clear()
    search.clear()
    statistics.clear()
    health.clear()

    assert all(json.loads(json.dumps(snapshot.to_dict())) for snapshot in snapshots)
    assert len(snapshots[0].entries) == len(snapshots[1].publishers) == 1
    assert len(snapshots[2].packages) == len(snapshots[3].versions) == 1
    assert (
        len(snapshots[4].results)
        == len(snapshots[5].records)
        == len(snapshots[6].checks)
        == 1
    )


def test_close_events_are_idempotent_and_instances_remain_isolated() -> None:
    statistics = _statistics_service()
    health = ReferenceHealthService()
    health.register_check(HealthCheck("health"))
    other_statistics = ReferenceStatisticsService()
    other_health = ReferenceHealthService()
    statistics.close()
    statistics.close()
    health.close()
    health.close()

    assert statistics.snapshot().events[-1].event_type.value == "closed"
    assert health.snapshot().events[-1].event_type.value == "closed"
    assert sum(event.event_type.value == "closed" for event in statistics.events()) == 1
    assert sum(event.event_type.value == "closed" for event in health.events()) == 1
    assert other_statistics.snapshot().records == ()
    assert other_health.snapshot().checks == ()


def test_bounded_reference_writes_are_thread_safe_without_hidden_services() -> None:
    service = ReferenceHealthService()

    def register(index: int) -> str:
        identifier = f"check-{index:02d}"
        service.register_check(HealthCheck(identifier))
        service.update_result(
            HealthResult(HealthCheckId(identifier), HealthStatus.HEALTHY)
        )
        return identifier

    with ThreadPoolExecutor(max_workers=8) as executor:
        identifiers = tuple(executor.map(register, range(32)))

    assert len(set(identifiers)) == 32
    assert service.statistics().healthy == 32
