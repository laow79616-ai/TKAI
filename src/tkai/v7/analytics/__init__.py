"""Analytics sink contracts."""

from __future__ import annotations

from typing import Protocol


class AnalyticsSink(Protocol):
    """Accepts local analytics events."""

    def record(self, name: str, value: object) -> None: ...


__all__ = ("AnalyticsSink",)
