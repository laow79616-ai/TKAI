"""Opt-in Policy Engine adapter for adaptive ranking and outcome recording."""

from __future__ import annotations

from tkai.policy import PolicyContext, PolicyDecision

from .manager import AdaptiveRoutingManager
from .models import ProviderSignal


class AdaptiveRoutingPolicyAdapter:
    """Expose adaptive routing through explicit policy stages without recursion."""

    def __init__(
        self,
        manager: AdaptiveRoutingManager,
        *,
        priority: int = 0,
        allow_provider_override: bool = False,
    ) -> None:
        self.manager = manager
        self._priority = priority
        self.allow_provider_override = allow_provider_override
        self._enabled = True

    def name(self) -> str:
        return "adaptive_routing"

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(detail={"adapter": "AdaptiveRoutingPolicyAdapter"})

    def apply(self, context: PolicyContext) -> None:
        candidates = context.data.get("adaptive_candidates")
        if isinstance(candidates, (list, tuple)) and all(
            isinstance(item, str) for item in candidates
        ):
            try:
                decision = self.manager.select_provider(candidates)
            except Exception:
                return
            context.data["adaptive_decision"] = decision
            if self.allow_provider_override and "provider" not in context.data:
                context.data["provider"] = decision.selected_provider
        signal = context.data.get("adaptive_signal")
        if isinstance(signal, ProviderSignal):
            self.manager.record_signal(signal)

    def shutdown(self) -> None:
        self._enabled = False
