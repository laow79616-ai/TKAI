"""Read-only server version route adapter."""

from __future__ import annotations

from collections.abc import Callable
from importlib import import_module

from ..dependencies import ApiDependencies


def endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind version data to an application-specific configuration."""

    def version() -> dict[str, object]:
        return {
            "server_version": dependencies.server_config.version.value,
            "framework_version": _framework_version(),
            "build_metadata": dict(dependencies.server_config.metadata.values),
        }

    return version


def _framework_version() -> str:
    """Read the installed TKAI version without making it a Server type dependency."""
    package = import_module("tkai")
    value = getattr(package, "__version__", "unknown")
    return str(value)
