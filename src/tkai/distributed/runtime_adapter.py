"""Explicit adapters for LocalCoordinator, Runtime callers, and Policy Engine."""

from __future__ import annotations

from tkai.policy import PolicyContext, PolicyDecision

from .coordinator import DistributedCoordinator


class DistributedRuntimeAdapter:
    """Start and stop a caller-supplied coordinator without changing Runtime APIs."""

    def __init__(self, coordinator: DistributedCoordinator) -> None:
        self.coordinator = coordinator

    def start(self) -> None:
        """Explicitly start the local coordinator."""
        self.coordinator.start()

    def stop(self) -> None:
        """Explicitly stop the local coordinator."""
        self.coordinator.stop()

    def health(self) -> dict[str, object]:
        """Return local coordinator diagnostics."""
        return self.coordinator.summary()


class DistributedPolicyAdapter:
    """Put a coordinator in an explicit PolicyContext without auto-starting it."""

    def __init__(
        self,
        coordinator: DistributedCoordinator,
        *,
        name: str = "distributed",
        priority: int = 0,
    ) -> None:
        self.coordinator = coordinator
        self._name = name
        self._priority = priority
        self._enabled = True

    def name(self) -> str:
        return self._name

    def priority(self) -> int:
        return self._priority

    def enabled(self) -> bool:
        return self._enabled

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        return PolicyDecision(
            detail={"backend": type(self.coordinator.backend).__name__}
        )

    def apply(self, context: PolicyContext) -> None:
        context.data["distributed_coordinator"] = self.coordinator

    def shutdown(self) -> None:
        self._enabled = False
