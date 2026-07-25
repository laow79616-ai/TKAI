"""Retry policy and exception classification kept independent of providers."""

from __future__ import annotations

from collections.abc import Callable

from .models import ExceptionClassification, RetryBudget, RetryDecision
from .strategy import BackoffStrategy, FixedBackoffStrategy

ExceptionClassifier = Callable[[Exception], ExceptionClassification]


def classify_exception(error: Exception) -> ExceptionClassification:
    """Classify common local failures without requiring a provider dependency."""
    if isinstance(error, TimeoutError):
        return ExceptionClassification.TIMEOUT
    if isinstance(error, ConnectionError):
        return ExceptionClassification.TRANSIENT
    name = type(error).__name__.lower()
    if "timeout" in name:
        return ExceptionClassification.TIMEOUT
    if "rate" in name and "limit" in name:
        return ExceptionClassification.RATE_LIMIT
    if "connection" in name or "network" in name or "temporary" in name:
        return ExceptionClassification.TRANSIENT
    return ExceptionClassification.PERMANENT


class RetryPolicy:
    """One explicit retry policy; default configuration performs no retry."""

    def __init__(
        self,
        name: str = "default",
        *,
        max_attempts: int = 1,
        backoff: BackoffStrategy | None = None,
        classifier: ExceptionClassifier = classify_exception,
    ) -> None:
        if not name or max_attempts < 1:
            raise ValueError(
                "policy name must not be empty and max_attempts must be positive"
            )
        self.name = name
        self.max_attempts = max_attempts
        self.backoff = backoff or FixedBackoffStrategy()
        self.classifier = classifier

    def budget(self) -> RetryBudget:
        """Create an operation-local budget; policy instances retain no state."""
        return RetryBudget(maximum=self.max_attempts - 1)

    def decide(
        self, error: Exception, attempt: int, budget: RetryBudget
    ) -> RetryDecision:
        """Return a safe decision without sleeping, provider calls, or mutation."""
        classification = self.classifier(error)
        if classification not in {
            ExceptionClassification.TRANSIENT,
            ExceptionClassification.TIMEOUT,
            ExceptionClassification.RATE_LIMIT,
        }:
            return RetryDecision(
                False, classification=classification, reason="permanent failure"
            )
        if attempt >= self.max_attempts or not budget.remaining:
            return RetryDecision(
                False, classification=classification, reason="retry budget exhausted"
            )
        return RetryDecision(
            True,
            self.backoff.delay(attempt),
            classification,
            "retryable failure",
        )
