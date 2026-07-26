"""Offline contract tests for the optional Marketplace Server FastAPI host."""

from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

from server import ApiRequest, Pagination
from server.api import ApiDependencies, create_app
from server.api.errors import ApiValidationError, map_error
from server.health import HealthCheck, HealthError, HealthStatus, ReferenceHealthService
from server.package import (
    PackageCategory,
    PackageDescriptor,
    PackageId,
    PackageManifest,
    PackageRecord,
    PackageVersionRef,
)
from server.publisher import (
    PublisherDescriptor,
    PublisherId,
    PublisherProfile,
    PublisherRecord,
)
from server.registry import (
    RegistryCoordinate,
    RegistryDescriptor,
    RegistryEntry,
    RegistryId,
)
from server.search import (
    ReferenceSearchService,
    ReferenceSearchStorage,
    SearchEntry,
    SearchTarget,
)
from server.version import VersionDescriptor, VersionId, VersionManifest, VersionRecord


class FakeFastAPI:
    """In-process FastAPI-compatible recorder that never opens a socket."""

    def __init__(self, **metadata: object) -> None:
        self.metadata = metadata
        self.state = SimpleNamespace()
        self.routes: list[tuple[str, tuple[str, ...], object, tuple[str, ...]]] = []
        self.middleware: list[object] = []
        self.exception_handlers: list[object] = []

    def add_api_route(
        self,
        path: str,
        endpoint: object,
        *,
        methods: list[str],
        tags: list[str],
        **_metadata: object,
    ) -> None:
        self.routes.append((path, tuple(methods), endpoint, tuple(tags)))

    def add_middleware(self, middleware: object, **_kwargs: object) -> None:
        self.middleware.append(middleware)

    def add_exception_handler(self, error: object, handler: object) -> None:
        self.exception_handlers.append((error, handler))


def fake_factory(**kwargs: object) -> FakeFastAPI:
    """Inject a test host without importing FastAPI."""
    return FakeFastAPI(**kwargs)


def _routes(app: FakeFastAPI) -> dict[str, object]:
    return {path: endpoint for path, _methods, endpoint, _tags in app.routes}


def test_create_app_registers_read_only_routes_openapi_and_middleware() -> None:
    """One app instance has its own dependencies and no write endpoints."""
    dependencies = ApiDependencies.create()
    app = create_app(dependencies=dependencies, app_factory=fake_factory)

    assert isinstance(app, FakeFastAPI)
    assert app.state.api_dependencies is dependencies
    assert app.metadata["docs_url"] == "/docs"
    assert app.metadata["openapi_url"] == "/openapi.json"
    assert {
        "/health",
        "/health/live",
        "/health/ready",
        "/health/startup",
        "/metrics",
        "/version",
        "/metadata",
        "/registry",
        "/registry/{registry_id}",
        "/publishers",
        "/publishers/{publisher_id}",
        "/packages",
        "/packages/{package_id}",
        "/versions",
        "/versions/{version_id}",
        "/search",
        "/statistics",
        "/auth/login",
        "/auth/me",
        "/auth/logout",
    }.issubset({route[0] for route in app.routes})
    assert all(
        route[1] == ("GET",)
        for route in app.routes
        if route[0]
        in {
            "/health",
            "/version",
            "/metadata",
            "/registry",
            "/publishers",
            "/packages",
            "/versions",
            "/search",
            "/statistics",
        }
    )
    assert len(app.middleware) == 5
    assert app.exception_handlers


def test_read_only_endpoints_delegate_to_explicit_reference_dependencies() -> None:
    """Endpoints return only supplied local Foundation state and metadata."""
    health = ReferenceHealthService()
    health.register_check(HealthCheck("reference", HealthStatus.HEALTHY))
    dependencies = replace(ApiDependencies.create(), health_service=health)
    app = create_app(dependencies=dependencies, app_factory=fake_factory)
    routes = _routes(app)

    health_data = routes["/health"]()
    version_data = routes["/version"]()
    metadata_data = routes["/metadata"]()

    assert health_data["checks"][0]["name"] == "reference"
    assert version_data["server_version"] == "6.0"
    assert version_data["framework_version"] == "3.0.0"
    assert metadata_data["server_name"] == "tkai-marketplace-server"
    assert metadata_data["supported_modules"] == list(dependencies.supported_modules)


def test_multiple_apps_are_isolated_and_legacy_api_contracts_remain_available() -> None:
    """Application composition creates no singleton state and preserves V6 contracts."""
    first = ApiDependencies.create()
    first.health_service.register_check(HealthCheck("one", HealthStatus.HEALTHY))
    second = ApiDependencies.create()

    one = create_app(dependencies=first, app_factory=fake_factory)
    two = create_app(dependencies=second, app_factory=fake_factory)

    assert _routes(one)["/health"]()["checks"][0]["name"] == "one"
    assert _routes(two)["/health"]()["checks"] == []
    assert ApiRequest(pagination=Pagination(limit=1)).pagination.limit == 1


def test_error_mapping_is_stable_and_real_host_requires_optional_fastapi() -> None:
    """Known Foundation errors map safely while FastAPI remains optional."""
    mapped = map_error(HealthError("offline failure"))
    assert mapped.status_code == 400
    assert mapped.error.code == "HealthError"

    with pytest.raises(RuntimeError, match="FastAPI is required"):
        create_app()


def test_resource_routes_use_reference_services_only_and_return_json_models() -> None:
    """Resource list/get routes delegate through the injected Reference Services."""
    dependencies = ApiDependencies.create()
    dependencies.registry_service.create(
        RegistryEntry(
            RegistryId("registry-1"),
            RegistryDescriptor(RegistryCoordinate("publisher-1", "package-1", "1.0")),
        )
    )
    dependencies.publisher_service.create(
        PublisherRecord(
            PublisherId("publisher-1"), PublisherDescriptor(PublisherProfile("One"))
        )
    )
    dependencies.package_service.create(
        PackageRecord(
            PackageId("package-1"),
            PackageManifest(
                PackageDescriptor("publisher-1", "One", PackageCategory.TOOL),
                PackageVersionRef("1.0"),
            ),
        )
    )
    dependencies.version_service.create(
        VersionRecord(
            VersionId("version-1"),
            VersionManifest(VersionDescriptor("package-1", "publisher-1", "1.0")),
        )
    )
    dependencies = replace(
        dependencies,
        search_service=ReferenceSearchService(
            ReferenceSearchStorage(
                (
                    SearchEntry(
                        "search-1",
                        SearchTarget.PACKAGE,
                        "One",
                        publisher="publisher-1",
                        package="package-1",
                        category="tool",
                    ),
                )
            )
        ),
    )
    routes = _routes(create_app(dependencies=dependencies, app_factory=fake_factory))

    assert routes["/registry"]()["total"] == 1
    assert (
        routes["/registry/{registry_id}"]("registry-1")["data"]["registry_id"]
        == "registry-1"
    )
    assert routes["/publishers"]()["total"] == 1
    assert (
        routes["/publishers/{publisher_id}"]("publisher-1")["data"]["publisher_id"]
        == "publisher-1"
    )
    assert routes["/packages"]()["total"] == 1
    assert (
        routes["/packages/{package_id}"]("package-1")["data"]["package_id"]
        == "package-1"
    )
    assert routes["/versions"]()["total"] == 1
    assert (
        routes["/versions/{version_id}"]("version-1")["data"]["version_id"]
        == "version-1"
    )
    assert routes["/search"](keyword="one", target="package")["total"] == 1
    assert routes["/statistics"]()["data"]["counters"]["total_sources"] == 0


def test_search_query_validation_maps_to_a_safe_http_contract() -> None:
    """Invalid query values are rejected without touching Foundation state."""
    routes = _routes(
        create_app(dependencies=ApiDependencies.create(), app_factory=fake_factory)
    )

    with pytest.raises(ApiValidationError):
        routes["/search"](target="invalid")
    assert (
        map_error(ApiValidationError("Invalid search query parameters.")).status_code
        == 400
    )
