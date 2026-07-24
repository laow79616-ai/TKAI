"""Explicit per-application dependency composition for the HTTP API."""

from __future__ import annotations

from dataclasses import dataclass, field

from server.health import ReferenceHealthService
from server.models import ServerConfig


@dataclass(frozen=True, slots=True)
class ApiDependencies:
    """Reference services explicitly injected into one application instance."""

    health_service: ReferenceHealthService
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
        return cls(health_service=ReferenceHealthService())
