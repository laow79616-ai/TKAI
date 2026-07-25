"""Explicit Policy Engine adapter for telemetry manager access."""

from tkai.policy import PolicyContext, PolicyDecision

from .manager import TelemetryManager


class TelemetryPolicyAdapter:
    def __init__(self, manager: TelemetryManager, *, priority: int = 0) -> None:
        self.manager = manager
        self._priority = priority
        self._enabled = True

    def name(self) -> str:
        return "telemetry"

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(
            detail={"exporter_count": len(self.manager.registry.list())}
        )

    def apply(self, context: PolicyContext) -> None:
        context.data["telemetry_manager"] = self.manager

    def shutdown(self) -> None:
        self._enabled = False
