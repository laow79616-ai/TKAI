"""Transport-neutral mappings for Marketplace Server Foundation errors."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from typing import TypeAlias

from .models import ApiError


@dataclass(frozen=True, slots=True)
class ApiException:
    """Mapped HTTP status and serializable error payload."""

    status_code: int
    error: ApiError


FoundationErrorType: TypeAlias = type[Exception]

_FOUNDATION_ERROR_PATHS = (
    ("server.health", "HealthError"),
    ("server.registry.errors", "RegistryError"),
    ("server.publisher.errors", "PublisherError"),
    ("server.package.errors", "PackageError"),
    ("server.version.errors", "VersionError"),
    ("server.search.errors", "SearchError"),
    ("server.statistics.errors", "StatisticsError"),
)


def foundation_error_types() -> tuple[FoundationErrorType, ...]:
    """Resolve registered error classes after package initialization is complete."""
    types: list[FoundationErrorType] = []
    for module_name, attribute in _FOUNDATION_ERROR_PATHS:
        error_type = getattr(import_module(module_name), attribute)
        if not isinstance(error_type, type) or not issubclass(error_type, Exception):
            raise TypeError(f"{module_name}.{attribute} is not an exception type.")
        types.append(error_type)
    return tuple(types)


def map_error(error: Exception) -> ApiException:
    """Map known Foundation errors without exposing implementation details."""
    if isinstance(error, foundation_error_types()):
        return ApiException(400, ApiError(type(error).__name__, str(error)))
    return ApiException(500, ApiError("internal_error", "Internal server error."))


async def foundation_exception_handler(_request: object, error: Exception) -> object:
    """Create a FastAPI response lazily so importing contracts needs no FastAPI."""
    mapped = map_error(error)
    try:
        response_module = import_module("starlette.responses")
        response_type = response_module.JSONResponse
    except ModuleNotFoundError as exc:
        raise RuntimeError("FastAPI is required to serve API errors.") from exc
    return response_type(status_code=mapped.status_code, content=mapped.error.to_dict())
