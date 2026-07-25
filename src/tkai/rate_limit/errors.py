"""Typed errors for local provider rate limit management."""


class RateLimitError(RuntimeError):
    """Base error for quota and rate limiter operations."""


class QuotaNotFoundError(RateLimitError):
    """Raised when a provider/scope quota has not been registered."""
