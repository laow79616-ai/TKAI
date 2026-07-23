"""Local region role topology with deterministic, explicit grouping."""

from __future__ import annotations

from threading import RLock

from .models import Region
from .regions import RegionRole


class RegionTopology:
    """Assign roles without starting health checks or migration workflows."""

    def __init__(self) -> None:
        self._roles: dict[str, RegionRole] = {}
        self._lock = RLock()

    def set_role(self, region_id: str, role: RegionRole) -> None:
        with self._lock:
            self._roles[region_id] = role

    def group(self, role: RegionRole) -> tuple[str, ...]:
        with self._lock:
            return tuple(
                sorted(name for name, value in self._roles.items() if value is role)
            )

    def priority(self, region: Region) -> tuple[int, int, str]:
        """Return a stable topology and static-priority sort key."""
        role = self._roles.get(region.region_id, RegionRole.PRIMARY)
        order = {
            RegionRole.PRIMARY: 0,
            RegionRole.SECONDARY: 1,
            RegionRole.BACKUP: 2,
            RegionRole.DISABLED: 3,
        }[role]
        return (order, -region.priority, region.region_id)

    def eligible(self, region: Region) -> bool:
        return (
            self._roles.get(region.region_id, RegionRole.PRIMARY)
            is not RegionRole.DISABLED
        )

    def snapshot(self) -> dict[str, str]:
        with self._lock:
            return {name: self._roles[name].value for name in sorted(self._roles)}
