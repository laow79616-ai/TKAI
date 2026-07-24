"""Bounded offline benchmarks for Marketplace Server V6 reference foundations."""

from __future__ import annotations

from collections.abc import Callable

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
    RegistryQuery,
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
    StatisticsQuery,
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

from .base import BenchmarkRunner
from .models import BenchmarkResult
from .report import BenchmarkReport


def _runner(iterations: int) -> BenchmarkRunner:
    return BenchmarkRunner(warmup=1, iterations=iterations, random_seed=6_008)


def _registry(identifier: str = "registry") -> RegistryEntry:
    return RegistryEntry(
        RegistryId(identifier),
        RegistryDescriptor(RegistryCoordinate("publisher", identifier, "1.0.0")),
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


def benchmark_registry_create(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceRegistryService().create(_registry())
    )


def benchmark_registry_list_search(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceRegistryService()
        service.create(_registry())
        service.list()
        return service.search(RegistryQuery())

    return _runner(iterations).run(operation)


def benchmark_publisher_create_search(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferencePublisherService()
        service.create(_publisher())
        return service.search()

    return _runner(iterations).run(operation)


def benchmark_package_create_search(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferencePackageService()
        service.create(_package())
        return service.search()

    return _runner(iterations).run(operation)


def benchmark_version_create_search(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceVersionService()
        service.create(_version())
        return service.search()

    return _runner(iterations).run(operation)


def benchmark_unified_search(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceSearchService(
            ReferenceSearchStorage(
                (SearchEntry("package", SearchTarget.PACKAGE, "package"),)
            )
        ).search(SearchQuery("package"))
    )


def benchmark_statistics_record_query_aggregate(
    iterations: int = 10,
) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceStatisticsService()
        service.register_source(
            StatisticsSource("source", StatisticsSourceType.CUSTOM, "source")
        )
        service.record(
            StatisticsRecord(
                "record",
                "source",
                StatisticsMetric("items", StatisticsMetricType.COUNTER),
                StatisticsValue(1),
            )
        )
        service.query(StatisticsQuery())
        return service.summarize()

    return _runner(iterations).run(operation)


def benchmark_health_update_snapshot(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceHealthService()
        service.register_check(HealthCheck("health"))
        service.update_result(
            HealthResult(HealthCheckId("health"), HealthStatus.HEALTHY)
        )
        return service.snapshot()

    return _runner(iterations).run(operation)


SERVER_BENCHMARKS: tuple[tuple[str, Callable[[int], BenchmarkResult]], ...] = (
    ("server.registry.create", benchmark_registry_create),
    ("server.registry.list_search", benchmark_registry_list_search),
    ("server.publisher.create_search", benchmark_publisher_create_search),
    ("server.package.create_search", benchmark_package_create_search),
    ("server.version.create_search", benchmark_version_create_search),
    ("server.search.unified", benchmark_unified_search),
    (
        "server.statistics.record_query_aggregate",
        benchmark_statistics_record_query_aggregate,
    ),
    ("server.health.update_snapshot", benchmark_health_update_snapshot),
)


def reports(iterations: int = 10) -> dict[str, dict[str, str]]:
    """Return stable Markdown and JSON report shapes for every local scenario."""
    return {
        name: {
            "markdown": BenchmarkReport.to_markdown(name, benchmark(iterations)),
            "json": BenchmarkReport.to_json(name, benchmark(iterations)),
        }
        for name, benchmark in SERVER_BENCHMARKS
    }


if __name__ == "__main__":
    name, benchmark = SERVER_BENCHMARKS[0]
    BenchmarkReport.emit(name, benchmark(10))
