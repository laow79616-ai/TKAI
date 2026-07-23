"""Public facade for optional policy registration, execution, and diagnostics."""

from __future__ import annotations

import builtins

from tkai.observability import EventBus

from .engine import PolicyEngine
from .interfaces import Policy as PolicyProtocol
from .models import PolicyContext, PolicyExecution
from .pipeline import PolicyPipeline
from .registry import PolicyRegistry


class PolicyManager:
    """Own one policy registry and engine without taking over existing managers."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self.registry = PolicyRegistry()
        self.engine = PolicyEngine(self.registry, event_bus=event_bus)
        self.pipeline = PolicyPipeline(self.engine)

    def register(self, policy: PolicyProtocol) -> None:
        """Register one explicit policy."""
        self.registry.register(policy)

    def unregister(self, name: str) -> PolicyProtocol:
        """Unregister one policy without implicit shutdown."""
        return self.registry.unregister(name)

    def get(self, name: str) -> PolicyProtocol:
        """Return one registered policy."""
        return self.registry.get(name)

    def list(self) -> builtins.list[PolicyProtocol]:
        """Return policies in stable execution order."""
        return self.registry.list()

    def enable(self, name: str) -> None:
        """Enable one registered policy."""
        self.registry.enable(name)

    def disable(self, name: str) -> None:
        """Disable one registered policy."""
        self.registry.disable(name)

    def execute(self, context: PolicyContext) -> tuple[PolicyExecution, ...]:
        """Execute an explicit policy context through the engine."""
        return self.engine.execute(context)

    def shutdown(self) -> None:
        """Shutdown policies with per-policy failure isolation."""
        self.engine.shutdown()

    def summary(self) -> builtins.list[dict[str, object]]:
        """Return safe policy metadata for CLI and Doctor presentation."""
        return [
            {
                "name": policy.name(),
                "priority": policy.priority(),
                "enabled": self.registry.enabled(policy.name()) and policy.enabled(),
                "type": type(policy).__name__,
            }
            for policy in self.list()
        ]
