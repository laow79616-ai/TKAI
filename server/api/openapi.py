"""OpenAPI metadata shared by the optional FastAPI application factory."""

from __future__ import annotations

from server.models import ServerConfig


def openapi_metadata(config: ServerConfig) -> dict[str, object]:
    """Return deterministic documentation metadata without mutable global state."""
    return {
        "title": config.name,
        "version": config.version.value,
        "description": "TKAI Marketplace Server reference HTTP API.",
        "openapi_tags": [
            {"name": "health", "description": "Reference health state."},
            {"name": "server", "description": "Server metadata and version."},
        ],
    }
