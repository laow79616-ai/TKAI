"""Read-only Registry route adapters."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies
from ..models import list_response, resource_response


def list_endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind stable Registry listing to the injected service."""

    def list_registries() -> dict[str, object]:
        return list_response(dependencies.registry_service.list())

    return list_registries


def get_endpoint(
    dependencies: ApiDependencies,
) -> Callable[[str], dict[str, object]]:
    """Bind Registry lookup to the injected service."""

    def get_registry(registry_id: str) -> dict[str, object]:
        return resource_response(dependencies.registry_service.get(registry_id))

    return get_registry
