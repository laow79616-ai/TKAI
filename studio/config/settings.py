"""Small immutable Studio configuration model without ambient environment reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


class StudioConfigurationError(ValueError):
    """Raised when an explicit Studio configuration value is invalid."""


@dataclass(frozen=True, slots=True)
class StudioSettings:
    """Configuration passed explicitly to a Studio backend application factory."""

    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8080
    session_ttl_seconds: int = 3_600

    def __post_init__(self) -> None:
        if not self.api_prefix.startswith("/"):
            raise StudioConfigurationError("Studio API prefix must begin with '/'.")
        if not self.host:
            raise StudioConfigurationError("Studio host must not be empty.")
        if not 1 <= self.port <= 65_535:
            raise StudioConfigurationError("Studio port must be between 1 and 65535.")
        if self.session_ttl_seconds < 1:
            raise StudioConfigurationError("Studio session TTL must be positive.")

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> StudioSettings:
        """Build settings from an explicit mapping without mutating its values."""
        allowed = {"api_prefix", "host", "port", "session_ttl_seconds"}
        unknown = set(values).difference(allowed)
        if unknown:
            raise StudioConfigurationError(
                f"Unknown Studio configuration fields: {sorted(unknown)}"
            )
        api_prefix = values.get("api_prefix", "/api")
        host = values.get("host", "127.0.0.1")
        port = values.get("port", 8080)
        session_ttl_seconds = values.get("session_ttl_seconds", 3_600)
        if not isinstance(api_prefix, str) or not isinstance(host, str):
            raise StudioConfigurationError(
                "Studio host and API prefix must be strings."
            )
        if not isinstance(port, int) or isinstance(port, bool):
            raise StudioConfigurationError("Studio port must be an integer.")
        if not isinstance(session_ttl_seconds, int) or isinstance(
            session_ttl_seconds, bool
        ):
            raise StudioConfigurationError("Studio session TTL must be an integer.")
        return cls(
            api_prefix=api_prefix,
            host=host,
            port=port,
            session_ttl_seconds=session_ttl_seconds,
        )
