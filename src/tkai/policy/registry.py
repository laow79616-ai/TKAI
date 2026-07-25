"""Thread-safe registry for policies owned by an optional Policy Engine."""

from __future__ import annotations

from threading import RLock

from .errors import PolicyNotFoundError, PolicyRegistrationError
from .interfaces import Policy


class PolicyRegistry:
    """Store policies once and return them in stable priority/name order."""

    def __init__(self) -> None:
        self._policies: dict[str, Policy] = {}
        self._enabled: set[str] = set()
        self._lock = RLock()

    def register(self, policy: Policy) -> None:
        """Register a policy with a non-empty unique name."""
        name = policy.name()
        if not name:
            raise PolicyRegistrationError("policy name must not be empty")
        with self._lock:
            if name in self._policies:
                raise PolicyRegistrationError(f"Policy '{name}' is already registered")
            self._policies[name] = policy
            if policy.enabled():
                self._enabled.add(name)

    def unregister(self, name: str) -> Policy:
        """Remove and return a policy without invoking its shutdown hook."""
        with self._lock:
            try:
                policy = self._policies.pop(name)
            except KeyError as error:
                raise PolicyNotFoundError(
                    f"Policy '{name}' is not registered"
                ) from error
            self._enabled.discard(name)
            return policy

    def get(self, name: str) -> Policy:
        """Return a named policy or a clear typed error."""
        with self._lock:
            try:
                return self._policies[name]
            except KeyError as error:
                raise PolicyNotFoundError(
                    f"Policy '{name}' is not registered"
                ) from error

    def list(self) -> list[Policy]:
        """Return policies by descending priority then ascending name."""
        with self._lock:
            return sorted(
                self._policies.values(),
                key=lambda policy: (-policy.priority(), policy.name()),
            )

    def enable(self, name: str) -> None:
        """Enable one registered policy without changing its implementation."""
        self.get(name)
        with self._lock:
            self._enabled.add(name)

    def disable(self, name: str) -> None:
        """Disable one registered policy without calling its shutdown hook."""
        self.get(name)
        with self._lock:
            self._enabled.discard(name)

    def enabled(self, name: str) -> bool:
        """Return registry-level enabled state for a registered policy."""
        self.get(name)
        with self._lock:
            return name in self._enabled
