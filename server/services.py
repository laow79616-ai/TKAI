"""Pure-memory reference services for the Marketplace Server architecture."""

from __future__ import annotations

from .health import HealthCheck, HealthReport, HealthSnapshot, HealthStatus
from .models import ServerSnapshot, ServerStatistics
from .release import ReleaseManifest, ReleasePolicy, ReleaseSnapshot
from .search import SearchQuery, SearchResult, SearchSnapshot
from .storage import ReferenceStorage


class _ReferenceService:
    def __init__(self) -> None:
        self._storage = ReferenceStorage()
        self._closed = False

    def register(self, identifier: str, item: object) -> object:
        self._ensure_open()
        return self._storage.put(identifier, item)

    def get(self, identifier: str) -> object:
        self._ensure_open()
        return self._storage.get(identifier)

    def list(self) -> tuple[object, ...]:
        self._ensure_open()
        return self._storage.list()

    def snapshot(self) -> object:
        return self.list()

    def close(self) -> None:
        self._closed = True

    def _ensure_open(self) -> None:
        if self._closed:
            raise RuntimeError("Reference server service is closed.")


class ReferenceRegistryService(_ReferenceService):
    """Reference Registry service with caller-provided, local descriptions only."""


class ReferencePublisherService(_ReferenceService):
    """Reference Publisher service with caller-provided, local descriptions only."""


class ReferencePackageService(_ReferenceService):
    """Reference Package service with caller-provided, local descriptions only."""


class ReferenceVersionService(_ReferenceService):
    """Reference Version service with caller-provided, local descriptions only."""


class ReferenceSearchService:
    """Return explicit local result declarations; this is not a search engine."""

    def __init__(self, result: SearchResult | None = None) -> None:
        self._result = result or SearchResult()
        self._snapshot = SearchSnapshot()
        self._closed = False

    def search(self, query: SearchQuery) -> SearchResult:
        if self._closed:
            raise RuntimeError("Reference search service is closed.")
        self._snapshot = SearchSnapshot(query, self._result)
        return self._result

    def snapshot(self) -> SearchSnapshot:
        return self._snapshot

    def close(self) -> None:
        self._closed = True


class ReferenceStatisticsService:
    """Calculate count-only statistics from explicit reference service snapshots."""

    def snapshot(
        self,
        *,
        registries: int = 0,
        publishers: int = 0,
        packages: int = 0,
        versions: int = 0,
        releases: int = 0,
        search_documents: int = 0,
    ) -> ServerStatistics:
        return ServerStatistics(
            registries, publishers, packages, versions, releases, search_documents
        )


class ReferenceReleaseService(_ReferenceService):
    """Store release descriptors only; it cannot publish or install packages."""

    def __init__(self, policy: ReleasePolicy | None = None) -> None:
        super().__init__()
        self._policy = policy or ReleasePolicy()

    def register_release(self, manifest: ReleaseManifest) -> ReleaseManifest:
        if (
            manifest.descriptor.channel.value == "general_availability"
            and not self._policy.allow_general_availability
        ):
            raise ValueError("General availability release is disabled by policy.")
        registered = self.register(manifest.descriptor.release_id, manifest)
        if not isinstance(registered, ReleaseManifest):
            raise TypeError("Reference release storage returned an invalid manifest.")
        return registered

    def snapshot(self) -> ReleaseSnapshot:
        releases = tuple(
            item for item in self.list() if isinstance(item, ReleaseManifest)
        )
        return ReleaseSnapshot(releases)


class ReferenceHealthService:
    """Expose caller-supplied passive checks without probing any dependency."""

    def __init__(self, checks: tuple[HealthCheck, ...] = ()) -> None:
        self._report = HealthReport(checks)

    def report(self) -> HealthReport:
        return self._report

    def snapshot(self) -> HealthSnapshot:
        return HealthSnapshot(self._report)

    @classmethod
    def healthy(cls) -> ReferenceHealthService:
        return cls((HealthCheck("reference_storage", HealthStatus.PASS),))


def server_snapshot(
    statistics: ServerStatistics, snapshot: ServerSnapshot
) -> ServerSnapshot:
    """Create a snapshot with explicitly supplied immutable server information."""
    return ServerSnapshot(snapshot.info, statistics, snapshot.closed)
