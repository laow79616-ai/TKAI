"""Explicit adapters for Runtime-adjacent and Policy Engine retry use."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tkai.policy import PolicyContext, PolicyDecision

from .manager import RetryManager
from .policy import RetryPolicy

T = TypeVar("T")


class RuntimeRetryAdapter:
    """Offer an explicit retry call helper without modifying ProviderRuntime."""

    def __init__(self, manager: RetryManager, policy: RetryPolicy | str) -> None:
        self.manager = manager
        self.policy = policy

    def run(
        self,
        operation: Callable[[], T],
        *,
        sleep: Callable[[float], None] = lambda _: None,
    ) -> T:
        """Run one caller-provided operation through the explicit RetryManager."""
        return self.manager.run(operation, policy=self.policy, sleep=sleep)


class RetryPolicyAdapter:
    """Expose a RetryManager to an explicit Policy Engine pipeline context."""

    def __init__(
        self, manager: RetryManager, *, name: str = "retry", priority: int = 0
    ) -> None:
        self.manager = manager
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
            detail={"retry_policy_count": len(self.manager.summary())}
        )

    def apply(self, context: PolicyContext) -> None:
        context.data["retry_manager"] = self.manager

    def shutdown(self) -> None:
        self._enabled = False
