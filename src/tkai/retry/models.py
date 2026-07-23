"""Immutable, provider-neutral retry decisions and local budgets."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExceptionClassification(str, Enum):
    """Safe retry classifications independent of any one provider SDK."""

    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    PERMANENT = "permanent"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """One explainable decision after a failed operation attempt."""

    retry: bool
    delay_seconds: float = 0.0
    classification: ExceptionClassification = ExceptionClassification.UNKNOWN
    reason: str = ""


@dataclass(frozen=True, slots=True)
class RetryAttempt:
    """Safe attempt outcome retained for diagnostics and observability."""

    attempt: int
    classification: ExceptionClassification
    will_retry: bool
    delay_seconds: float


@dataclass(frozen=True, slots=True)
class RetryBudget:
    """Immutable per-operation retry budget; callers explicitly replace it."""

    maximum: int = 0
    consumed: int = 0

    def __post_init__(self) -> None:
        if self.maximum < 0 or self.consumed < 0:
            raise ValueError("retry budget values must not be negative")
        if self.consumed > self.maximum:
            raise ValueError("retry budget consumption exceeds maximum")

    @property
    def remaining(self) -> int:
        """Return retry capacity remaining for this explicit operation."""
        return self.maximum - self.consumed

    def consume(self) -> RetryBudget:
        """Return a replacement budget after one permitted retry."""
        if not self.remaining:
            from .errors import RetryBudgetExhaustedError

            raise RetryBudgetExhaustedError("retry budget is exhausted")
        return RetryBudget(self.maximum, self.consumed + 1)
