"""Thread-safe reference License service with no enforcement or persistence."""

from __future__ import annotations

from threading import RLock

from .errors import LicenseNotFoundError
from .models import CapabilitySnapshot, LicenseEntitlement


class ReferenceLicenseService:
    """Returns injected immutable entitlements only; no feature is controlled."""

    def __init__(self, entitlements: tuple[LicenseEntitlement, ...] = ()) -> None:
        self._items = {item.entitlement_id: item for item in entitlements}
        self._lock = RLock()

    def get(self, entitlement_id: str) -> LicenseEntitlement:
        with self._lock:
            try:
                return self._items[entitlement_id]
            except KeyError as exc:
                raise LicenseNotFoundError(entitlement_id) from exc

    def snapshot(self) -> tuple[LicenseEntitlement, ...]:
        with self._lock:
            return tuple(self._items[key] for key in sorted(self._items))

    def capabilities(self, entitlement_id: str) -> CapabilitySnapshot:
        item = self.get(entitlement_id)
        return CapabilitySnapshot(item.edition)
