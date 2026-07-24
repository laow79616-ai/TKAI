"""Optional, read-only FastAPI host and transport-neutral Server API contracts."""

from .models import (
    ApiError,
    ApiRequest,
    ApiResponse,
    ApiVersion,
    Filtering,
    Pagination,
    Sorting,
)


def __getattr__(name: str) -> object:
    """Load optional host helpers only after transport contracts are available."""
    if name == "create_app":
        from .app import create_app

        return create_app
    if name == "ApiDependencies":
        from .dependencies import ApiDependencies

        return ApiDependencies
    if name in {"ApiException", "map_error"}:
        from .errors import ApiException, map_error

        return {"ApiException": ApiException, "map_error": map_error}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = (
    "ApiDependencies",
    "ApiError",
    "ApiException",
    "ApiRequest",
    "ApiResponse",
    "ApiVersion",
    "Filtering",
    "Pagination",
    "Sorting",
    "create_app",
    "map_error",
)
