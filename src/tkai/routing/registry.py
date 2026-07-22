"""Thread-safe registry for immutable provider routing metadata."""

from __future__ import annotations

from threading import RLock

from .errors import ProviderMetadataNotFoundError, RoutingError
from .models import ProviderMetadata


class RoutingRegistry:
    """Maintain the single provider metadata collection used by routers."""

    def __init__(self) -> None:
        self._metadata: dict[str, ProviderMetadata] = {}
        self._lock = RLock()

    def register(self, metadata: ProviderMetadata) -> None:
        """Register immutable metadata, rejecting duplicate provider names."""
        with self._lock:
            if metadata.provider in self._metadata:
                raise RoutingError(
                    f"Routing metadata '{metadata.provider}' is already registered"
                )
            self._metadata[metadata.provider] = metadata

    def get(self, provider: str) -> ProviderMetadata:
        """Return provider metadata or raise a typed missing-metadata error."""
        with self._lock:
            try:
                return self._metadata[provider]
            except KeyError as error:
                raise ProviderMetadataNotFoundError(
                    f"Routing metadata '{provider}' is not registered"
                ) from error

    def list(self) -> list[ProviderMetadata]:
        """Return metadata in deterministic provider-name order."""
        with self._lock:
            return [self._metadata[name] for name in sorted(self._metadata)]

    def remove(self, provider: str) -> ProviderMetadata:
        """Remove and return registered metadata."""
        with self._lock:
            value = self.get(provider)
            del self._metadata[provider]
            return value

    def clear(self) -> None:
        """Remove all registered metadata."""
        with self._lock:
            self._metadata.clear()
