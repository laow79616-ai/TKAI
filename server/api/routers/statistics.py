"""Read-only Statistics route adapter."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies
from ..models import resource_response


def endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind an immutable Statistics snapshot to the injected service."""

    def statistics() -> dict[str, object]:
        return resource_response(dependencies.statistics_service.snapshot())

    return statistics
