"""Projection-only V11 interfaces."""

from typing import Protocol


class ReadOnlyProjection(Protocol):
    def overview(self) -> dict[str, object]: ...


__all__ = ("ReadOnlyProjection",)
