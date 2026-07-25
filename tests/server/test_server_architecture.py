"""Offline tests for Marketplace Server V6 architecture contracts."""

import pytest

from server import (
    ApiRequest,
    HealthCheck,
    HealthStatus,
    Pagination,
    ReferenceHealthService,
    ReferencePackageService,
    ReferencePublisherService,
    ReferenceRegistryService,
    ReferenceReleaseService,
    ReferenceSearchService,
    ReferenceStatisticsService,
    ReferenceVersionService,
    ReleaseChannel,
    ReleaseDescriptor,
    ReleaseManifest,
    SearchQuery,
    SearchResult,
    ServerCapability,
    ServerConfig,
    ServerInfo,
    ServerMetadata,
    ServerSnapshot,
    ServerStatus,
)


def test_server_models_are_immutable_and_defensively_copy_metadata() -> None:
    values = {"scope": "reference"}
    metadata = ServerMetadata(values)
    values["scope"] = "changed"
    info = ServerInfo(
        "marketplace-server",
        ServerConfig().version,
        ServerStatus.READY,
        (ServerCapability("registry"),),
        metadata,
    )
    assert ServerInfo.__dataclass_params__.frozen is True
    assert info.metadata.values["scope"] == "reference"
    assert ServerSnapshot(info).closed is False


def test_api_contracts_validate_pagination_and_keep_request_metadata_immutable() -> (
    None
):
    with pytest.raises(ValueError):
        Pagination(limit=0)
    values = {"request": "local"}
    request = ApiRequest(metadata=values)
    values["request"] = "changed"
    assert request.metadata["request"] == "local"


def test_reference_domain_services_are_local_and_snapshot_stable() -> None:
    services = (
        ReferenceRegistryService(),
        ReferencePublisherService(),
        ReferencePackageService(),
        ReferenceVersionService(),
    )
    for index, service in enumerate(services):
        service.register(f"item-{index}", {"value": index})
        assert service.snapshot() == ({"value": index},)
        service.close()
        with pytest.raises(RuntimeError):
            service.list()


def test_search_statistics_release_and_health_reference_contracts() -> None:
    search = ReferenceSearchService(SearchResult(({"name": "example"},), 1))
    assert search.search(SearchQuery("example")).total == 1
    assert search.snapshot().query is not None
    statistics = ReferenceStatisticsService().snapshot(packages=1, versions=2)
    assert statistics.packages == 1 and statistics.versions == 2

    release = ReferenceReleaseService()
    candidate = ReleaseManifest(
        ReleaseDescriptor("candidate", "example", "1.0", ReleaseChannel.CANDIDATE)
    )
    assert release.register_release(candidate) == candidate
    with pytest.raises(ValueError):
        release.register_release(
            ReleaseManifest(
                ReleaseDescriptor(
                    "ga", "example", "1.0", ReleaseChannel.GENERAL_AVAILABILITY
                )
            )
        )
    health = ReferenceHealthService((HealthCheck("storage", HealthStatus.PASS),))
    assert health.snapshot().report.checks[0].status is HealthStatus.PASS
