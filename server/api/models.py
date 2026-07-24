"""Immutable transport-neutral contracts for the Marketplace Server HTTP API."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


def _copy(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a read-only defensive copy suitable for an API contract."""
    return MappingProxyType(dict(value))


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
