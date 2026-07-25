"""Immutable filters for an explicit multi-region selection call."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Region


@dataclass(frozen=True, slots=True)
class RegionPolicy:
    """Apply caller-selected regional constraints without changing defaults."""

    preferred_regions: tuple[str, ...] = ()
    excluded_regions: frozenset[str] = frozenset()
    minimum_health: bool = True
    minimum_priority: int | None = None
    allow_fallback: bool = True

    def allows(self, region: Region) -> bool:
        if region.region_id in self.excluded_regions:
            return False
        if self.minimum_health and not region.healthy:
            return False
        if (
            self.minimum_priority is not None
            and region.priority < self.minimum_priority
        ):
            return False
        return True
