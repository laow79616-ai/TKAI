"""Small immutable Studio configuration model without ambient environment reads."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast


class StudioConfigurationError(ValueError):
    """Raised when an explicit Studio configuration value is invalid."""


@dataclass(frozen=True, slots=True)
class StudioSettings:
    """Configuration passed explicitly to a Studio backend application factory."""

    app_name: str = "TKAI Studio"
    app_version: str = "7.0.0"
    environment: str = "development"
    api_prefix: str = "/api"
    host: str = "127.0.0.1"
    port: int = 8080
    debug: bool = False
    docs_enabled: bool = True
    cors_origins: tuple[str, ...] = ()
    request_timeout: float = 30.0
    execution_timeout: float = 300.0
    storage_mode: str = "memory"
    log_level: str = "INFO"
    session_ttl_seconds: int = 3_600

    def __post_init__(self) -> None:
        if not self.app_name or not self.app_version or not self.environment:
            raise StudioConfigurationError(
                "Studio application metadata must not be empty."
            )
        if not self.api_prefix.startswith("/"):
            raise StudioConfigurationError("Studio API prefix must begin with '/'.")
        if not self.host:
            raise StudioConfigurationError("Studio host must not be empty.")
        if not 1 <= self.port <= 65_535:
            raise StudioConfigurationError("Studio port must be between 1 and 65535.")
        if self.session_ttl_seconds < 1:
            raise StudioConfigurationError("Studio session TTL must be positive.")
        if self.request_timeout <= 0 or self.execution_timeout <= 0:
            raise StudioConfigurationError("Studio timeouts must be positive.")
        if self.storage_mode != "memory":
            raise StudioConfigurationError(
                "Only reference memory storage is available."
            )
        if not self.log_level:
            raise StudioConfigurationError("Studio log level must not be empty.")

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> StudioSettings:
        """Build settings from an explicit mapping without mutating its values."""
        allowed = {
            "app_name",
            "app_version",
            "environment",
            "api_prefix",
            "host",
            "port",
            "debug",
            "docs_enabled",
            "cors_origins",
            "request_timeout",
            "execution_timeout",
            "storage_mode",
            "log_level",
            "session_ttl_seconds",
        }
        unknown = set(values).difference(allowed)
        if unknown:
            raise StudioConfigurationError(
                f"Unknown Studio configuration fields: {sorted(unknown)}"
            )
        app_name = values.get("app_name", "TKAI Studio")
        app_version = values.get("app_version", "7.0.0")
        environment = values.get("environment", "development")
        api_prefix = values.get("api_prefix", "/api")
        host = values.get("host", "127.0.0.1")
        port = values.get("port", 8080)
        debug = values.get("debug", False)
        docs_enabled = values.get("docs_enabled", True)
        cors_origins = values.get("cors_origins", ())
        request_timeout = values.get("request_timeout", 30.0)
        execution_timeout = values.get("execution_timeout", 300.0)
        storage_mode = values.get("storage_mode", "memory")
        log_level = values.get("log_level", "INFO")
        session_ttl_seconds = values.get("session_ttl_seconds", 3_600)
        strings = (
            app_name,
            app_version,
            environment,
            api_prefix,
            host,
            storage_mode,
            log_level,
        )
        if not all(isinstance(value, str) for value in strings):
            raise StudioConfigurationError(
                "Studio string configuration values must be strings."
            )
        if not isinstance(port, int) or isinstance(port, bool):
            raise StudioConfigurationError("Studio port must be an integer.")
        if not isinstance(debug, bool) or not isinstance(docs_enabled, bool):
            raise StudioConfigurationError(
                "Studio boolean configuration values must be bool."
            )
        if not isinstance(cors_origins, (tuple, list)) or not all(
            isinstance(origin, str) for origin in cors_origins
        ):
            raise StudioConfigurationError("Studio CORS origins must be string values.")
        if not isinstance(request_timeout, (int, float)) or isinstance(
            request_timeout, bool
        ):
            raise StudioConfigurationError("Studio request timeout must be numeric.")
        if not isinstance(execution_timeout, (int, float)) or isinstance(
            execution_timeout, bool
        ):
            raise StudioConfigurationError("Studio execution timeout must be numeric.")
        if not isinstance(session_ttl_seconds, int) or isinstance(
            session_ttl_seconds, bool
        ):
            raise StudioConfigurationError("Studio session TTL must be an integer.")
        return cls(
            app_name=cast(str, app_name),
            app_version=cast(str, app_version),
            environment=cast(str, environment),
            api_prefix=cast(str, api_prefix),
            host=cast(str, host),
            port=port,
            debug=debug,
            docs_enabled=docs_enabled,
            cors_origins=tuple(cors_origins),
            request_timeout=float(request_timeout),
            execution_timeout=float(execution_timeout),
            storage_mode=cast(str, storage_mode),
            log_level=cast(str, log_level),
            session_ttl_seconds=session_ttl_seconds,
        )
