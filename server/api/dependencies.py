"""Explicit per-application dependency composition for the HTTP API."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from server.models import ServerConfig

if TYPE_CHECKING:
    from server.api.auth import ReferenceAuthenticationService
    from server.enterprise import ReferenceEnterpriseService
    from server.health import ReferenceHealthService
    from server.package import ReferencePackageService
    from server.publisher import ReferencePublisherService
    from server.registry import ReferenceRegistryService
    from server.search import ReferenceSearchService
    from server.statistics import ReferenceStatisticsService
    from server.version import ReferenceVersionService


@dataclass(frozen=True, slots=True)
class ApiDependencies:
    """Reference services explicitly injected into one application instance."""

    health_service: ReferenceHealthService
    authentication_service: ReferenceAuthenticationService
    registry_service: ReferenceRegistryService
    publisher_service: ReferencePublisherService
    package_service: ReferencePackageService
    version_service: ReferenceVersionService
    search_service: ReferenceSearchService
    statistics_service: ReferenceStatisticsService
    enterprise_service: ReferenceEnterpriseService = field(
        default_factory=lambda: __import__(
            "server.enterprise", fromlist=["ReferenceEnterpriseService"]
        ).ReferenceEnterpriseService()
    )
    server_config: ServerConfig = field(default_factory=ServerConfig)
    supported_modules: tuple[str, ...] = (
        "registry",
        "publisher",
        "package",
        "version",
        "search",
        "statistics",
        "health",
    )

    @classmethod
    def create(cls) -> ApiDependencies:
        """Create isolated in-memory defaults without accessing storage directly."""
        from server.api.auth import ReferenceAuthenticationService
        from server.enterprise import ReferenceEnterpriseService
        from server.health import ReferenceHealthService
        from server.package import ReferencePackageService
        from server.publisher import ReferencePublisherService
        from server.registry import ReferenceRegistryService
        from server.search import ReferenceSearchService
        from server.statistics import ReferenceStatisticsService
        from server.version import ReferenceVersionService

        return cls(
            health_service=ReferenceHealthService(),
            authentication_service=ReferenceAuthenticationService(),
            registry_service=ReferenceRegistryService(),
            publisher_service=ReferencePublisherService(),
            package_service=ReferencePackageService(),
            version_service=ReferenceVersionService(),
            search_service=ReferenceSearchService(),
            statistics_service=ReferenceStatisticsService(),
            enterprise_service=ReferenceEnterpriseService(),
        )
