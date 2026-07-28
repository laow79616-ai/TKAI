"""Read-only bounded analytical adapter contracts."""

from __future__ import annotations

from typing import Any, Protocol


class ReadOnlyAnalyticsPort(Protocol):
    def read(
        self, source: str, filters: dict[str, Any], limit: int
    ) -> list[dict[str, Any]]: ...


class BoundedTestDouble:
    def __init__(self, rows: list[dict[str, Any]] | None = None) -> None:
        self.rows = rows or []

    def read(
        self, source: str, filters: dict[str, Any], limit: int
    ) -> list[dict[str, Any]]:
        del source
        return [
            dict(row)
            for row in self.rows
            if all(row.get(k) == v for k, v in filters.items())
        ][:limit]
