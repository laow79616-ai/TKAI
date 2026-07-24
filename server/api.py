"""REST-shaped contracts only; this module does not implement HTTP transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


def _copy(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class ApiVersion:
    value: str = "v1"


@dataclass(frozen=True, slots=True)
class Pagination:
    offset: int = 0
    limit: int = 20

    def __post_init__(self) -> None:
        if self.offset < 0 or self.limit < 1:
            raise ValueError(
                "Pagination offset must be non-negative and limit positive."
            )


@dataclass(frozen=True, slots=True)
class Filtering:
    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))


@dataclass(frozen=True, slots=True)
class Sorting:
    field: str = "id"
    descending: bool = False


@dataclass(frozen=True, slots=True)
class ApiRequest:
    version: ApiVersion = field(default_factory=ApiVersion)
    pagination: Pagination = field(default_factory=Pagination)
    filtering: Filtering = field(default_factory=Filtering)
    sorting: Sorting = field(default_factory=Sorting)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _copy(self.metadata))


@dataclass(frozen=True, slots=True)
class ApiError:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class ApiResponse:
    data: object | None = None
    error: ApiError | None = None
    request_id: str | None = None
