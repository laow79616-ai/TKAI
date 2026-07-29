"""Planner contracts without business-domain policy."""

from __future__ import annotations

from typing import Protocol


class Planner(Protocol):
    """Produces an explicit plan from local input."""

    def plan(self, request: object) -> tuple[object, ...]: ...


__all__ = ("Planner",)
