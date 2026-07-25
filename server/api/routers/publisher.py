"""Read-only Publisher route adapters."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies
from ..models import list_response, resource_response


def list_endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind stable Publisher listing to the injected service."""

    def list_publishers() -> dict[str, object]:
        return list_response(dependencies.publisher_service.list())

    return list_publishers


def get_endpoint(
    dependencies: ApiDependencies,
) -> Callable[[str], dict[str, object]]:
    """Bind Publisher lookup to the injected service."""

    def get_publisher(publisher_id: str) -> dict[str, object]:
        return resource_response(dependencies.publisher_service.get(publisher_id))

    return get_publisher
