"""Failure-isolated optional policy execution over explicit pipeline stages."""

from __future__ import annotations

from tkai.observability import EventBus

from .events import PolicyEvent, PolicyExecuted, PolicyFailed, PolicySkipped
from .models import PolicyContext, PolicyExecution
from .registry import PolicyRegistry


class PolicyEngine:
    """Execute registered policies without altering provider runtime defaults."""

    def __init__(
        self,
        registry: PolicyRegistry | None = None,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry or PolicyRegistry()
        self.event_bus = event_bus
        self.events: list[PolicyEvent] = []

    def execute(self, context: PolicyContext) -> tuple[PolicyExecution, ...]:
        """Evaluate policies in stable order and isolate each policy failure."""
        executions: list[PolicyExecution] = []
        for policy in self.registry.list():
            name = policy.name()
            if not self.registry.enabled(name) or not policy.enabled():
                executions.append(
                    PolicyExecution(name, context.stage, "skipped", "disabled")
                )
                self._publish(
                    PolicySkipped(
                        policy=name, stage=context.stage.value, reason="disabled"
                    )
                )
                continue
            try:
                decision = policy.evaluate(context)
                if not decision.allowed:
                    executions.append(
                        PolicyExecution(name, context.stage, "skipped", decision.reason)
                    )
                    self._publish(
                        PolicySkipped(
                            policy=name,
                            stage=context.stage.value,
                            reason=decision.reason,
                        )
                    )
                    continue
                policy.apply(context)
            except Exception as error:
                reason = type(error).__name__
                executions.append(
                    PolicyExecution(name, context.stage, "failed", reason)
                )
                self._publish(
                    PolicyFailed(policy=name, stage=context.stage.value, reason=reason)
                )
                continue
            executions.append(
                PolicyExecution(name, context.stage, "executed", decision.reason)
            )
            self._publish(
                PolicyExecuted(
                    policy=name, stage=context.stage.value, reason=decision.reason
                )
            )
        return tuple(executions)

    def shutdown(self) -> None:
        """Shutdown every policy once, isolating individual policy failures."""
        for policy in self.registry.list():
            try:
                policy.shutdown()
            except Exception as error:
                self._publish(
                    PolicyFailed(
                        policy=policy.name(),
                        stage="shutdown",
                        reason=type(error).__name__,
                    )
                )

    def _publish(self, event: PolicyEvent) -> None:
        self.events.append(event)
        if self.event_bus is not None:
            try:
                self.event_bus.publish(event)
            except Exception:
                return
