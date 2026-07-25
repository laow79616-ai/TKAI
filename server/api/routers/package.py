"""Read-only Package route adapters."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies
from ..models import list_response, resource_response


def list_endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind stable Package listing to the injected service."""

    def list_packages() -> dict[str, object]:
        return list_response(dependencies.package_service.list())

    return list_packages


def get_endpoint(
    dependencies: ApiDependencies,
) -> Callable[[str], dict[str, object]]:
    """Bind Package lookup to the injected service."""

    def get_package(package_id: str) -> dict[str, object]:
        return resource_response(dependencies.package_service.get(package_id))

    return get_package
