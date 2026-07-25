"""Protocol contracts and compatibility adapters for the Policy Engine."""

from __future__ import annotations

from typing import Protocol

from .models import PolicyContext, PolicyDecision


class Policy(Protocol):
    """Optional policy contract; implementations must not own provider execution."""

    def name(self) -> str:
        """Return the unique stable policy name."""

    def priority(self) -> int:
        """Return a higher-first priority used with name as a stable tie-breaker."""

    def enabled(self) -> bool:
        """Return whether the engine may evaluate this policy."""

    def evaluate(self, context: PolicyContext) -> PolicyDecision:
        """Decide whether the policy should be applied to this context."""

    def apply(self, context: PolicyContext) -> None:
        """Apply local context changes after a successful evaluation."""

    def shutdown(self) -> None:
        """Release optional local resources; calls must be safe to repeat."""


class _CompatibilityAdapter:
    """Expose an existing policy-like object without changing its implementation."""

    def __init__(self, target: object, *, name: str, priority: int = 0) -> None:
        self.target = target
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
        return PolicyDecision(detail={"adapter": type(self.target).__name__})

    def apply(self, context: PolicyContext) -> None:
        context.data.setdefault("policies", {})[self._name] = self.target

    def shutdown(self) -> None:
        self._enabled = False


class RoutingPolicyAdapter(_CompatibilityAdapter):
    """Adapt existing routing policy objects for explicit pipeline use."""

    def __init__(self, target: object, *, priority: int = 0) -> None:
        super().__init__(target, name="routing", priority=priority)


class BreakerPolicyAdapter(_CompatibilityAdapter):
    """Adapt existing circuit-breaker strategy objects without lifecycle changes."""

    def __init__(self, target: object, *, priority: int = 0) -> None:
        super().__init__(target, name="breaker", priority=priority)


class RateLimitPolicyAdapter(_CompatibilityAdapter):
    """Adapt existing local rate-limit strategies for opt-in policy pipelines."""

    def __init__(self, target: object, *, priority: int = 0) -> None:
        super().__init__(target, name="rate_limit", priority=priority)


class CachePolicyAdapter(_CompatibilityAdapter):
    """Adapt existing cache policies for opt-in policy pipelines."""

    def __init__(self, target: object, *, priority: int = 0) -> None:
        super().__init__(target, name="cache", priority=priority)


class PluginPolicyAdapter(_CompatibilityAdapter):
    """Adapt existing plugin managers or hook policies without auto-dispatch."""

    def __init__(self, target: object, *, priority: int = 0) -> None:
        super().__init__(target, name="plugin", priority=priority)
