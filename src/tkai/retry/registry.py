"""Thread-safe registry for explicit retry policies."""

from __future__ import annotations

from threading import RLock

from .errors import RetryPolicyNotFoundError, RetryPolicyRegistrationError
from .policy import RetryPolicy


class RetryRegistry:
    """Store named retry policies without creating any default provider wiring."""

    def __init__(self) -> None:
        self._policies: dict[str, RetryPolicy] = {}
        self._lock = RLock()

    def register(self, policy: RetryPolicy) -> None:
        """Register one unique local retry policy."""
        with self._lock:
            if policy.name in self._policies:
                raise RetryPolicyRegistrationError(
                    f"Retry policy '{policy.name}' exists"
                )
            self._policies[policy.name] = policy

    def unregister(self, name: str) -> RetryPolicy:
        """Remove and return a policy by name."""
        with self._lock:
            try:
                return self._policies.pop(name)
            except KeyError as error:
                raise RetryPolicyNotFoundError(
                    f"Retry policy '{name}' is not registered"
                ) from error

    def get(self, name: str) -> RetryPolicy:
        """Return a policy by name."""
        with self._lock:
            try:
                return self._policies[name]
            except KeyError as error:
                raise RetryPolicyNotFoundError(
                    f"Retry policy '{name}' is not registered"
                ) from error

    def list(self) -> list[RetryPolicy]:
        """Return policies in deterministic name order."""
        with self._lock:
            return [self._policies[name] for name in sorted(self._policies)]
