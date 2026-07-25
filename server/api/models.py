"""Immutable transport-neutral contracts for the Marketplace Server HTTP API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError


def _copy(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a read-only defensive copy suitable for an API contract."""
    return MappingProxyType(dict(value))


class ApiValidationError(ValueError):
    """Raised when an HTTP query does not satisfy its Pydantic contract."""


@dataclass(frozen=True, slots=True)
class ApiVersion:
    """Version marker for the transport contract, independent of package version."""

    value: str = "v1"


@dataclass(frozen=True, slots=True)
class Pagination:
    """Validated pagination request parameters."""

    offset: int = 0
    limit: int = 20

    def __post_init__(self) -> None:
        if self.offset < 0 or self.limit < 1:
            raise ValueError(
                "Pagination offset must be non-negative and limit positive."
            )


@dataclass(frozen=True, slots=True)
class Filtering:
    """Read-only filtering declarations."""

    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))


@dataclass(frozen=True, slots=True)
class Sorting:
    """Stable sorting declaration."""

    field: str = "id"
    descending: bool = False


@dataclass(frozen=True, slots=True)
class ApiRequest:
    """Legacy generic request contract retained for Server Foundation compatibility."""

    version: ApiVersion = field(default_factory=ApiVersion)
    pagination: Pagination = field(default_factory=Pagination)
    filtering: Filtering = field(default_factory=Filtering)
    sorting: Sorting = field(default_factory=Sorting)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _copy(self.metadata))


@dataclass(frozen=True, slots=True)
class ApiError:
    """Stable error payload used by exception mappings."""

    code: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


@dataclass(frozen=True, slots=True)
class ApiResponse:
    """Legacy response envelope retained without binding callers to FastAPI."""

    data: object | None = None
    error: ApiError | None = None
    request_id: str | None = None

    def to_dict(self) -> dict[str, object | None]:
        return {
            "data": self.data,
            "error": self.error.to_dict() if self.error is not None else None,
            "request_id": self.request_id,
        }


class ApiListResponse(BaseModel):
    """OpenAPI response schema for a deterministic list of resource records."""

    model_config = ConfigDict(frozen=True)

    data: list[dict[str, Any]] = Field(default_factory=list)
    total: int = Field(ge=0)
    error: None = None


class ApiResourceResponse(BaseModel):
    """OpenAPI response schema for one immutable resource record."""

    model_config = ConfigDict(frozen=True)

    data: dict[str, Any]
    error: None = None


class ApiErrorResponse(BaseModel):
    """OpenAPI response schema for stable, non-sensitive API errors."""

    model_config = ConfigDict(frozen=True)

    error: dict[str, str]


class SearchParameters(BaseModel):
    """Validated read-only unified Search query parameters."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keyword: str = Field(default="", max_length=256)
    target: str | None = Field(
        default=None, pattern="^(registry|publisher|package|version)$"
    )
    publisher: str | None = Field(default=None, max_length=256)
    package: str | None = Field(default=None, max_length=256)
    category: str | None = Field(default=None, max_length=256)
    tag: str | None = Field(default=None, max_length=256)
    version: str | None = Field(default=None, max_length=256)
    status: str | None = Field(default=None, max_length=256)


def validate_search_parameters(values: Mapping[str, object]) -> SearchParameters:
    """Validate query data and retain a transport-neutral public error type."""
    try:
        return SearchParameters.model_validate(dict(values))
    except ValidationError as error:
        raise ApiValidationError("Invalid search query parameters.") from error


def list_response(
    items: tuple[object, ...], *, total: int | None = None
) -> dict[str, object]:
    """Create a uniform JSON-ready list response from immutable Foundation data."""
    data = [_to_dict(item) for item in items]
    return ApiListResponse(
        data=data, total=len(data) if total is None else total
    ).model_dump()


def resource_response(item: object) -> dict[str, object]:
    """Create a uniform JSON-ready single-resource response."""
    return ApiResourceResponse(data=_to_dict(item)).model_dump()


def _to_dict(item: object) -> dict[str, Any]:
    method = getattr(item, "to_dict", None)
    if not callable(method):
        raise TypeError("API resources must expose a JSON-ready to_dict method.")
    value = method()
    if not isinstance(value, dict):
        raise TypeError("API resource to_dict must return a dictionary.")
    return value
