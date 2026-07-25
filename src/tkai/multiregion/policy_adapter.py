"""Opt-in Policy Engine integration for region selection context only."""

from tkai.policy import PolicyContext, PolicyDecision

from .manager import MultiRegionManager


class MultiRegionPolicyAdapter:
    """Store an explicit regional decision in PolicyContext without recursion."""

    def __init__(self, manager: MultiRegionManager, *, priority: int = 0) -> None:
        self.manager = manager
        self._priority = priority
        self._enabled = True

    def name(self) -> str:
        return "multiregion"

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(detail={"adapter": "MultiRegionPolicyAdapter"})

    def apply(self, context: PolicyContext) -> None:
        fixed = context.data.get("fixed_region")
        if fixed is not None and not isinstance(fixed, str):
            return
        try:
            context.data["region_decision"] = self.manager.select_region(
                fixed_region=fixed
            )
        except Exception:
            return

    def shutdown(self) -> None:
        self._enabled = False
