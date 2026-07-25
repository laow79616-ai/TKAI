"""Explicit adapter that leaves the existing Runtime public surface unchanged."""

from .manager import MultiRegionManager
from .models import RegionDecision


class MultiRegionRuntimeAdapter:
    """Offer an application-controlled region selection call before routing."""

    def __init__(self, manager: MultiRegionManager) -> None:
        self.manager = manager

    def select_region(
        self,
        *,
        fixed_region: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RegionDecision:
        return self.manager.select_region(
            fixed_region=fixed_region,
            required_capabilities=required_capabilities,
        )

    def shutdown(self) -> None:
        """Release no external resource; manager lifecycle remains caller-owned."""
