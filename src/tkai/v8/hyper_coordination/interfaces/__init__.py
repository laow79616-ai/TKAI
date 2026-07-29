"""Typing interfaces for read-only coordination projections."""

from __future__ import annotations

from typing import Protocol


class CoordinationReader(Protocol):
    def overview(self) -> dict[str, object]: ...

    def health(self) -> dict[str, object]: ...

    def metrics(self) -> dict[str, object]: ...


__all__ = ("CoordinationReader",)
