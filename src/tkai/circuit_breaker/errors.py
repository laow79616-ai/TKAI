"""Circuit breaker errors with no provider payload or secret data."""


class CircuitBreakerError(RuntimeError):
    """Base error for circuit breaker operations."""


class CircuitBreakerNotFoundError(CircuitBreakerError):
    """Raised when a requested provider has no registered breaker."""
