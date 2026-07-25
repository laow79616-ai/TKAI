"""Passive local Studio health service; it performs no external probe."""

from __future__ import annotations

from collections.abc import Mapping

from ..gateway import SDKStudioGateway


class HealthService:
    """Report readiness of explicitly composed Studio services and repositories."""

    def __init__(
        self, gateway: SDKStudioGateway, repositories: Mapping[str, object]
    ) -> None:
        self._gateway = gateway
        self._repositories = dict(repositories)

    def report(self) -> dict[str, object]:
        """Return a local readiness report without a network health check."""
        repositories = {
            name: bool(getattr(repository, "ready", lambda: False)())
            for name, repository in sorted(self._repositories.items())
        }
        return {
            "status": "ok" if all(repositories.values()) else "degraded",
            "gateway_ready": self._gateway.ready,
            "repositories": repositories,
        }
