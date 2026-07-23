"""Optional, explicit, provider-neutral retry framework."""

from .adapter import RetryPolicyAdapter, RuntimeRetryAdapter
from .errors import (
    RetryBudgetExhaustedError,
    RetryError,
    RetryPolicyNotFoundError,
    RetryPolicyRegistrationError,
)
from .events import RetryEvent, RetryExhausted, RetryScheduled
from .manager import RetryManager
from .models import ExceptionClassification, RetryAttempt, RetryBudget, RetryDecision
from .policy import RetryPolicy, classify_exception
from .registry import RetryRegistry
from .strategy import BackoffStrategy, ExponentialBackoffStrategy, FixedBackoffStrategy

__all__ = (
    "BackoffStrategy",
    "ExceptionClassification",
    "ExponentialBackoffStrategy",
    "FixedBackoffStrategy",
    "RetryAttempt",
    "RetryBudget",
    "RetryBudgetExhaustedError",
    "RetryDecision",
    "RetryError",
    "RetryEvent",
    "RetryExhausted",
    "RetryManager",
    "RetryPolicy",
    "RetryPolicyAdapter",
    "RetryPolicyNotFoundError",
    "RetryPolicyRegistrationError",
    "RetryRegistry",
    "RetryScheduled",
    "RuntimeRetryAdapter",
    "classify_exception",
)
