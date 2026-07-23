"""Bounded, thread-safe, in-memory provider outcome history."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
from math import ceil
from threading import RLock

from .models import ProviderSignal, ProviderStatistics


class ProviderHistory:
    """Store a finite local signal history without request or response bodies."""

    def __init__(
        self,
        *,
        max_samples_per_provider: int = 100,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if max_samples_per_provider < 1:
            raise ValueError("max_samples_per_provider must be positive")
        self.max_samples_per_provider = max_samples_per_provider
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._signals: dict[str, deque[ProviderSignal]] = {}
        self._lock = RLock()

    def record(self, signal: ProviderSignal) -> None:
        """Add one result while keeping the provider history bounded."""
        with self._lock:
            samples = self._signals.setdefault(
                signal.provider,
                deque(maxlen=self.max_samples_per_provider),
            )
            samples.append(signal)

    def snapshot(self, provider: str | None = None) -> tuple[ProviderSignal, ...]:
        """Return signals in stable provider then chronological order."""
        with self._lock:
            if provider is not None:
                return tuple(self._signals.get(provider, ()))
            return tuple(
                signal
                for name in sorted(self._signals)
                for signal in self._signals[name]
            )

    def statistics(self, provider: str) -> ProviderStatistics:
        """Calculate deterministic local aggregates for one provider."""
        samples = self.snapshot(provider)
        if not samples:
            return ProviderStatistics(provider=provider)
        successes = sum(sample.success for sample in samples)
        count = len(samples)
        latencies = sorted(sample.latency_ms for sample in samples)
        index = max(0, ceil(0.95 * count) - 1)
        last = samples[-1]
        return ProviderStatistics(
            provider=provider,
            request_count=count,
            success_count=successes,
            failure_count=count - successes,
            success_rate=successes / count,
            error_rate=(count - successes) / count,
            average_latency_ms=sum(latencies) / count,
            p95_latency_ms=latencies[index],
            average_cost=sum(sample.cost for sample in samples) / count,
            current_load=last.load,
            last_updated=last.timestamp,
            sample_count=count,
        )

    def clear(self) -> None:
        """Clear every local signal; this has no effect on other subsystems."""
        with self._lock:
            self._signals.clear()

    def remove_provider(self, provider: str) -> None:
        """Forget one provider's bounded local history if it exists."""
        with self._lock:
            self._signals.pop(provider, None)
