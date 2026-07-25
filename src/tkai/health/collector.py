"""Passive outcome collection; no network operations."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

from .evaluator import HealthEvaluator
from .events import HealthEvent
from .models import HealthStatus
from .registry import HealthRegistry


class PassiveHealthCollector:
    def __init__(
        self, registry: HealthRegistry, evaluator: HealthEvaluator | None = None
    ) -> None:
        self.registry = registry
        self.evaluator = evaluator or HealthEvaluator()
        self.events: list[HealthEvent] = []

    def success(self, provider: str) -> None:
        self._record(provider, True, False)

    def failure(self, provider: str) -> None:
        self._record(provider, False, False)

    def timeout(self, provider: str) -> None:
        self._record(provider, False, True)

    def _record(self, provider: str, success: bool, timeout: bool) -> None:
        old = self.registry.get(provider)
        now = datetime.now(timezone.utc)
        snapshot = replace(
            old,
            success_count=old.success_count + int(success),
            failure_count=old.failure_count + int(not success),
            timeout_count=old.timeout_count + int(timeout),
            consecutive_failures=0 if success else old.consecutive_failures + 1,
            last_success=now if success else old.last_success,
            last_failure=None if success else now,
            last_update=now,
        )
        snapshot = replace(snapshot, status=self.evaluator.evaluate(snapshot))
        self.registry.update(snapshot)
        if old.status != snapshot.status:
            event = "HealthChanged"
            if (
                snapshot.status is HealthStatus.HEALTHY
                and old.status is not HealthStatus.UNKNOWN
            ):
                event = "ProviderRecovered"
            elif snapshot.status is HealthStatus.DEGRADED:
                event = "ProviderDegraded"
            elif snapshot.status is HealthStatus.UNHEALTHY:
                event = "ProviderUnhealthy"
            self.events.append(
                HealthEvent(provider, event, old.status, snapshot.status, now)
            )
