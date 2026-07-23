"""Explicit retry execution facade; no ProviderManager or Runtime takeover."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from tkai.observability import EventBus

from .events import RetryEvent, RetryExhausted, RetryScheduled
from .models import RetryAttempt
from .policy import RetryPolicy
from .registry import RetryRegistry

T = TypeVar("T")


class RetryManager:
    """Execute caller-supplied operations only when explicitly invoked."""

    def __init__(
        self,
        registry: RetryRegistry | None = None,
        *,
        event_bus: EventBus | None = None,
    ) -> None:
        self.registry = registry or RetryRegistry()
        self.event_bus = event_bus
        self.events: list[RetryEvent] = []

    def register(self, policy: RetryPolicy) -> None:
        """Register one retry policy for explicit lookup."""
        self.registry.register(policy)

    def run(
        self,
        operation: Callable[[], T],
        *,
        policy: RetryPolicy | str,
        sleep: Callable[[float], None] = lambda _: None,
    ) -> T:
        """Run an operation with an injected sleeper and typed retry decisions."""
        selected = self.registry.get(policy) if isinstance(policy, str) else policy
        budget = selected.budget()
        for attempt in range(1, selected.max_attempts + 1):
            try:
                return operation()
            except Exception as error:
                decision = selected.decide(error, attempt, budget)
                record = RetryAttempt(
                    attempt,
                    decision.classification,
                    decision.retry,
                    decision.delay_seconds,
                )
                if not decision.retry:
                    self._publish(
                        RetryExhausted(
                            policy=selected.name,
                            attempt=attempt,
                            reason=record.classification.value,
                        )
                    )
                    raise
                budget = budget.consume()
                self._publish(
                    RetryScheduled(
                        policy=selected.name,
                        attempt=attempt,
                        reason=record.classification.value,
                    )
                )
                sleep(decision.delay_seconds)
        raise AssertionError("retry loop must return or raise")

    def summary(self) -> list[dict[str, object]]:
        """Return policy metadata for read-only CLI and Doctor diagnostics."""
        return [
            {
                "name": policy.name,
                "max_attempts": policy.max_attempts,
                "backoff": type(policy.backoff).__name__,
            }
            for policy in self.registry.list()
        ]

    def _publish(self, event: RetryEvent) -> None:
        self.events.append(event)
        if self.event_bus is not None:
            self.event_bus.publish(event)
