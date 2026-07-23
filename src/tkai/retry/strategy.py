"""Pluggable deterministic retry backoff strategies."""

from __future__ import annotations

from typing import Protocol


class BackoffStrategy(Protocol):
    """Return a non-negative delay for a one-based retry attempt number."""

    def delay(self, attempt: int) -> float:
        """Calculate a local delay without sleeping or doing I/O."""


class FixedBackoffStrategy:
    """Use one deterministic delay for every retry attempt."""

    def __init__(self, delay_seconds: float = 0.0) -> None:
        if delay_seconds < 0:
            raise ValueError("delay_seconds must not be negative")
        self.delay_seconds = delay_seconds

    def delay(self, attempt: int) -> float:
        """Return the configured constant delay after validating the attempt."""
        if attempt < 1:
            raise ValueError("attempt must be at least one")
        return self.delay_seconds


class ExponentialBackoffStrategy:
    """Use capped exponential delays without random jitter by default."""

    def __init__(
        self,
        base_delay: float = 0.0,
        multiplier: float = 2.0,
        maximum_delay: float = 60.0,
    ) -> None:
        if base_delay < 0 or multiplier < 1 or maximum_delay < 0:
            raise ValueError(
                "backoff values must be non-negative and multiplier at least one"
            )
        self.base_delay = base_delay
        self.multiplier = multiplier
        self.maximum_delay = maximum_delay

    def delay(self, attempt: int) -> float:
        """Return a capped delay for the one-based retry attempt."""
        if attempt < 1:
            raise ValueError("attempt must be at least one")
        return min(
            self.maximum_delay, self.base_delay * self.multiplier ** (attempt - 1)
        )
