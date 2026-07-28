"""Read-only server version route adapter."""

from __future__ import annotations

import os
from collections.abc import Callable
from importlib import import_module

from ..dependencies import ApiDependencies
from ..models import list_response, resource_response


def endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind version data to an application-specific configuration."""

    def version() -> dict[str, object]:
        return {
            "server_version": dependencies.server_config.version.value,
            "framework_version": _framework_version(),
            "build_metadata": dict(dependencies.server_config.metadata.values),
            "api_version": "v4",
            "release_date": os.getenv("TKAI_RELEASE_DATE", "2026-07-28"),
            "git_commit": os.getenv("TKAI_GIT_COMMIT", "development"),
        }

    return version


def _framework_version() -> str:
    """Read the installed TKAI version without making it a Server type dependency."""
    package = import_module("tkai")
    value = getattr(package, "__version__", "unknown")
    return str(value)


def list_endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind stable resource Version listing to the injected service."""

    def list_versions() -> dict[str, object]:
        return list_response(dependencies.version_service.list())

    return list_versions


def get_endpoint(
    dependencies: ApiDependencies,
) -> Callable[[str], dict[str, object]]:
    """Bind resource Version lookup to the injected service."""

    def get_version(version_id: str) -> dict[str, object]:
        return resource_response(dependencies.version_service.get(version_id))

    return get_version
