"""Thread-safe in-memory registry for provider circuit breakers."""

from __future__ import annotations

from threading import RLock

from .breaker import CircuitBreaker
from .errors import CircuitBreakerError, CircuitBreakerNotFoundError


class CircuitBreakerRegistry:
    """Own the only provider-to-breaker collection in the subsystem."""

    def __init__(self) -> None:
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = RLock()

    def register(
        self, provider: str, breaker: CircuitBreaker | None = None
    ) -> CircuitBreaker:
        """Register one breaker, rejecting duplicate provider registrations."""
        with self._lock:
            if provider in self._breakers:
                raise CircuitBreakerError(f"Breaker '{provider}' is already registered")
            value = breaker or CircuitBreaker(provider)
            if value.provider != provider:
                raise CircuitBreakerError(
                    "Breaker provider does not match registration"
                )
            self._breakers[provider] = value
            return value

    def get(self, provider: str) -> CircuitBreaker:
        """Return a registered breaker or raise a typed missing-breaker error."""
        with self._lock:
            try:
                return self._breakers[provider]
            except KeyError as error:
                raise CircuitBreakerNotFoundError(
                    f"Breaker '{provider}' is not registered"
                ) from error

    def list(self) -> list[CircuitBreaker]:
        """Return breakers in stable provider-name order."""
        with self._lock:
            return [self._breakers[name] for name in sorted(self._breakers)]

    def reset(self, provider: str) -> None:
        """Reset one registered breaker."""
        self.get(provider).reset()

    def clear(self) -> None:
        """Forget all registered breakers."""
        with self._lock:
            self._breakers.clear()
