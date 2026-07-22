"""Passive EventBus subscriber with bounded deterministic latency statistics."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from dataclasses import replace
from datetime import datetime, timezone
from math import ceil, isfinite
from threading import RLock
from typing import Any

from tkai.observability import Event, EventBus

from .errors import ProviderLoadNotFoundError
from .evaluator import LoadEvaluator
from .events import (
    LoadChanged,
    LoadEvent,
    ProviderLoadHigh,
    ProviderLoadRecovered,
    ProviderLoadReset,
    ProviderSaturated,
)
from .models import LoadStatus, ProviderLoadSnapshot
from .registry import LoadRegistry


class LatencyStatistics:
    """Bounded deterministic latency samples for one process-local provider."""

    def __init__(self, max_samples: int = 256) -> None:
        if max_samples < 1:
            raise ValueError("max_samples must be at least one")
        self._samples: deque[float] = deque(maxlen=max_samples)

    def add(self, latency_ms: float) -> None:
        """Add a non-negative finite latency sample."""
        if not isfinite(latency_ms) or latency_ms < 0:
            raise ValueError("latency_ms must be finite and non-negative")
        self._samples.append(latency_ms)

    def snapshot(self) -> tuple[float, float, float]:
        """Return average, P95, and P99 using deterministic nearest-rank values."""
        if not self._samples:
            return (0.0, 0.0, 0.0)
        values = sorted(self._samples)
        average = sum(values) / len(values)
        return (average, self._percentile(values, 0.95), self._percentile(values, 0.99))

    @staticmethod
    def _percentile(values: list[float], percentile: float) -> float:
        """Return a deterministic nearest-rank percentile for non-empty samples."""
        index = max(0, ceil(percentile * len(values)) - 1)
        return values[index]

    @property
    def size(self) -> int:
        """Return the retained bounded sample count."""
        return len(self._samples)


class PassiveLoadCollector:
    """Update local load snapshots only from supplied EventBus runtime events."""

    def __init__(
        self,
        registry: LoadRegistry,
        evaluator: LoadEvaluator | None = None,
        *,
        capacity: int = 10,
        max_latency_samples: int = 256,
        event_bus: EventBus | None = None,
    ) -> None:
        if capacity < 1:
            raise ValueError("capacity must be at least one")
        self.registry = registry
        self.evaluator = evaluator or LoadEvaluator()
        self.capacity = capacity
        self._max_latency_samples = max_latency_samples
        self._latencies: dict[str, LatencyStatistics] = {}
        self._lock = RLock()
        self.events: list[LoadEvent] = []
        self._event_bus: EventBus | None = None
        if event_bus is not None:
            self.subscribe(event_bus)

    def subscribe(self, event_bus: EventBus) -> None:
        """Subscribe once to the shared EventBus; no separate bus is created."""
        if self._event_bus is event_bus:
            return
        if self._event_bus is not None:
            self._event_bus.unsubscribe(self.handle)
        self._event_bus = event_bus
        event_bus.subscribe(self.handle)

    @property
    def event_bus(self) -> EventBus | None:
        """Return the shared subscribed EventBus, if collection is attached."""
        return self._event_bus

    def handle(self, event: Event) -> None:
        """Consume standard runtime events when they include a string provider name."""
        provider = event.data.get("provider")
        if not isinstance(provider, str) or not provider:
            return
        if event.name == "RequestStarted":
            self.request_started(provider)
        elif event.name == "RequestCompleted":
            self.request_completed(provider, self._latency(event.data))
        elif event.name == "ProviderFailed":
            self.request_failed(
                provider,
                timeout=bool(event.data.get("timeout", False)),
                latency_ms=self._latency(event.data),
            )

    def request_started(self, provider: str) -> ProviderLoadSnapshot:
        """Safely increment active requests from a passive start event."""
        return self._update(provider, active_delta=1)

    def request_completed(
        self, provider: str, latency_ms: float | None = None
    ) -> ProviderLoadSnapshot:
        """Safely decrement active work, count completion, and retain latency."""
        return self._update(
            provider,
            active_delta=-1,
            completed_delta=1,
            latency_ms=latency_ms,
        )

    def request_failed(
        self,
        provider: str,
        *,
        timeout: bool = False,
        latency_ms: float | None = None,
    ) -> ProviderLoadSnapshot:
        """Safely decrement active work and record failure or timeout statistics."""
        return self._update(
            provider,
            active_delta=-1,
            failed_delta=1,
            timeout_delta=int(timeout),
            latency_ms=latency_ms,
        )

    def reset(self, provider: str) -> ProviderLoadSnapshot:
        """Reset a snapshot and publish one reset event through the shared bus."""
        with self._lock:
            old = self._ensure(provider)
            snapshot = self.registry.reset(provider)
            self._latencies.pop(provider, None)
            self._publish(
                ProviderLoadReset(
                    provider=provider,
                    old_status=old.status,
                    new_status=snapshot.status,
                    snapshot=snapshot,
                    data={"provider": provider, "snapshot": snapshot.to_dict()},
                )
            )
            return snapshot

    def clear(self) -> None:
        """Clear registry snapshots and every bounded latency buffer."""
        with self._lock:
            self.registry.clear()
            self._latencies.clear()

    def _update(
        self,
        provider: str,
        *,
        active_delta: int = 0,
        completed_delta: int = 0,
        failed_delta: int = 0,
        timeout_delta: int = 0,
        latency_ms: float | None = None,
    ) -> ProviderLoadSnapshot:
        with self._lock:
            old = self._ensure(provider)
            statistics = self._statistics(provider)
            if latency_ms is not None:
                statistics.add(latency_ms)
            average, p95, p99 = statistics.snapshot()
            active = max(0, old.active_requests + active_delta)
            completed = old.completed_requests + completed_delta
            failed = old.failed_requests + failed_delta
            total = completed + failed
            snapshot = replace(
                old,
                active_requests=active,
                completed_requests=completed,
                failed_requests=failed,
                timeout_requests=old.timeout_requests + timeout_delta,
                average_latency_ms=average,
                p95_latency_ms=p95,
                p99_latency_ms=p99,
                error_rate=(failed / total) if total else 0.0,
                utilization=min(1.0, active / self.capacity),
                last_updated=datetime.now(timezone.utc),
            )
            snapshot = replace(snapshot, status=self.evaluator.evaluate(snapshot))
            self.registry.update(snapshot)
            if snapshot.status is not old.status:
                self._publish_transition(old, snapshot)
            return snapshot

    def _ensure(self, provider: str) -> ProviderLoadSnapshot:
        """Retrieve or register one provider snapshot as a local passive side effect."""
        try:
            return self.registry.get(provider)
        except ProviderLoadNotFoundError:
            return self.registry.register(provider)

    def _statistics(self, provider: str) -> LatencyStatistics:
        """Return the bounded latency tracker for one provider."""
        if provider not in self._latencies:
            self._latencies[provider] = LatencyStatistics(self._max_latency_samples)
        return self._latencies[provider]

    def _publish_transition(
        self, old: ProviderLoadSnapshot, snapshot: ProviderLoadSnapshot
    ) -> None:
        """Publish one status-change event, avoiding unchanged-event repetition."""
        event_class: type[LoadEvent] = LoadChanged
        if snapshot.status is LoadStatus.SATURATED:
            event_class = ProviderSaturated
        elif snapshot.status is LoadStatus.HIGH:
            event_class = ProviderLoadHigh
        elif old.status in {LoadStatus.HIGH, LoadStatus.SATURATED}:
            event_class = ProviderLoadRecovered
        self._publish(
            event_class(
                provider=snapshot.provider,
                old_status=old.status,
                new_status=snapshot.status,
                snapshot=snapshot,
                data={"provider": snapshot.provider, "snapshot": snapshot.to_dict()},
            )
        )

    def _publish(self, event: LoadEvent) -> None:
        """Retain event and optionally publish it to the shared existing EventBus."""
        self.events.append(event)
        if self._event_bus is not None:
            self._event_bus.publish(event)

    @staticmethod
    def _latency(data: Mapping[str, Any]) -> float | None:
        """Read an optional non-negative numeric latency value from event metadata."""
        value = data.get("latency_ms")
        if isinstance(value, (int, float)) and isfinite(value) and value >= 0:
            return float(value)
        return None
