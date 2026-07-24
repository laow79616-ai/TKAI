"""Read-only health route adapter."""

from __future__ import annotations

from collections.abc import Callable

from ..dependencies import ApiDependencies


def endpoint(dependencies: ApiDependencies) -> Callable[[], dict[str, object]]:
    """Bind a health endpoint to one explicitly supplied service container."""

    def health() -> dict[str, object]:
        return dependencies.health_service.snapshot().to_dict()

    return health
