"""Dashboard integration contracts only."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardContribution:
    """Metadata for a dashboard surface contributed by a V7 module."""

    module: str
    route: str
    title: str


__all__ = ("DashboardContribution",)
