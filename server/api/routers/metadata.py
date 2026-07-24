"""Read-only server metadata route adapter."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies


def endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind immutable descriptive metadata to one API application instance."""

    def metadata() -> dict[str, object]:
        config = dependencies.server_config
        return {
            "server_name": config.name,
            "server_description": "TKAI Marketplace Server reference foundation.",
            "supported_modules": list(dependencies.supported_modules),
            "foundation_version": config.version.value,
        }

    return metadata
