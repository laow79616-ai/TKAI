"""Thread-safe registry retaining immutable Region values only."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from .errors import MultiRegionError, RegionNotFoundError
from .models import Region


class RegionRegistry:
    """Own local region metadata with stable output order."""

    def __init__(self) -> None:
        self._regions: dict[str, Region] = {}
        self._lock = RLock()

    def register(self, region: Region) -> None:
        with self._lock:
            if region.region_id in self._regions:
                raise MultiRegionError(f"Region '{region.region_id}' is registered")
            self._regions[region.region_id] = region

    def unregister(self, region_id: str) -> Region:
        with self._lock:
            try:
                return self._regions.pop(region_id)
            except KeyError as error:
                raise RegionNotFoundError(
                    f"Region '{region_id}' is not registered"
                ) from error

    def get(self, region_id: str) -> Region:
        with self._lock:
            try:
                return self._regions[region_id]
            except KeyError as error:
                raise RegionNotFoundError(
                    f"Region '{region_id}' is not registered"
                ) from error

    def list(self) -> list[Region]:
        with self._lock:
            return [self._regions[name] for name in sorted(self._regions)]

    def enable(self, region_id: str) -> None:
        region = self.get(region_id)
        with self._lock:
            self._regions[region_id] = replace(region, enabled=True)

    def disable(self, region_id: str) -> None:
        region = self.get(region_id)
        with self._lock:
            self._regions[region_id] = replace(region, enabled=False)

    def snapshot(self) -> tuple[Region, ...]:
        return tuple(self.list())

    def clear(self) -> None:
        with self._lock:
            self._regions.clear()
