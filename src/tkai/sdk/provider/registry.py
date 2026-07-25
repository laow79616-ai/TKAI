"""Thread-safe provider client registry with deterministic capability lookup."""

from __future__ import annotations

from threading import RLock

from .capability import ProviderCapability
from .client import ProviderClient
from .errors import ProviderNotFoundError


class ProviderRegistry:
    """Own an explicit set of provider clients without creating default providers."""

    def __init__(self) -> None:
        self._clients: dict[str, ProviderClient] = {}
        self._lock = RLock()

    def register(self, client: ProviderClient) -> ProviderClient:
        """Register one uniquely named provider client."""
        with self._lock:
            if client.name in self._clients:
                raise ValueError(f"Provider already registered: {client.name}")
            self._clients[client.name] = client
        return client

    def unregister(self, name: str) -> ProviderClient:
        """Remove and return one provider client without closing it implicitly."""
        with self._lock:
            try:
                return self._clients.pop(name)
            except KeyError as error:
                raise ProviderNotFoundError(
                    f"Provider not registered: {name}"
                ) from error

    def lookup(self, name: str) -> ProviderClient:
        """Return one explicitly registered provider or a clear SDK error."""
        with self._lock:
            try:
                return self._clients[name]
            except KeyError as error:
                raise ProviderNotFoundError(
                    f"Provider not registered: {name}"
                ) from error

    def list(self) -> tuple[ProviderClient, ...]:
        """Return clients in stable name order without exposing internal mapping."""
        with self._lock:
            return tuple(self._clients[name] for name in sorted(self._clients))

    def supports(self, name: str, capability: ProviderCapability) -> bool:
        """Report whether one named provider declares a requested capability."""
        return capability in self.lookup(name).capabilities
