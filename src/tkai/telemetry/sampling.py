"""Deterministic, dependency-free span sampling strategies."""

from __future__ import annotations

from hashlib import sha256
from typing import Protocol


class Sampler(Protocol):
    """Decide whether a span should be recorded for one trace operation."""

    def should_sample(self, trace_id: str, operation: str) -> bool: ...


class AlwaysOnSampler:
    """Record every span, preserving the historical local telemetry behavior."""

    def should_sample(self, trace_id: str, operation: str) -> bool:
        del trace_id, operation
        return True


class AlwaysOffSampler:
    """Record no spans while leaving metrics and structured logs available."""

    def should_sample(self, trace_id: str, operation: str) -> bool:
        del trace_id, operation
        return False


class ProbabilitySampler:
    """Use stable hashing rather than process-random sampling decisions."""

    def __init__(self, rate: float = 1.0) -> None:
        if not 0.0 <= rate <= 1.0:
            raise ValueError("Sampling rate must be between 0.0 and 1.0.")
        self.rate = rate

    def should_sample(self, trace_id: str, operation: str) -> bool:
        if self.rate == 0.0:
            return False
        if self.rate == 1.0:
            return True
        sample = int.from_bytes(
            sha256(f"{trace_id}:{operation}".encode()).digest()[:8], "big"
        ) / float(2**64)
        return sample < self.rate
