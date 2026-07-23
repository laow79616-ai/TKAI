"""Explicit errors for the optional local Retry Framework."""


class RetryError(RuntimeError):
    """Base retry framework error."""


class RetryPolicyNotFoundError(RetryError):
    """Raised when a named retry policy is not registered."""


class RetryPolicyRegistrationError(RetryError):
    """Raised for duplicate or invalid retry policy registration."""


class RetryBudgetExhaustedError(RetryError):
    """Raised when a policy has no remaining local retry budget."""
