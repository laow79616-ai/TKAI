"""Thread-safe registry returning immutable provider load snapshots."""

from __future__ import annotations

from threading import RLock

from .errors import LoadError, ProviderLoadNotFoundError
from .models import ProviderLoadSnapshot


class LoadRegistry:
    """Maintain one immutable local snapshot per provider in stable order."""

    def __init__(self) -> None:
        self._snapshots: dict[str, ProviderLoadSnapshot] = {}
        self._lock = RLock()

    def register(self, provider: str) -> ProviderLoadSnapshot:
        """Register an initially unknown snapshot for a provider."""
        with self._lock:
            if provider in self._snapshots:
                raise LoadError(f"Load provider '{provider}' is already registered")
            snapshot = ProviderLoadSnapshot(provider)
            self._snapshots[provider] = snapshot
            return snapshot

    def get(self, provider: str) -> ProviderLoadSnapshot:
        """Return a read-only snapshot or raise a typed missing-provider error."""
        with self._lock:
            try:
                return self._snapshots[provider]
            except KeyError as error:
                raise ProviderLoadNotFoundError(
                    f"Load provider '{provider}' is not registered"
                ) from error

    def list(self) -> list[ProviderLoadSnapshot]:
        """Return snapshots sorted by provider name for deterministic callers."""
        with self._lock:
            return [self._snapshots[name] for name in sorted(self._snapshots)]

    def update(self, snapshot: ProviderLoadSnapshot) -> None:
        """Replace one registered snapshot; missing providers are explicit errors."""
        with self._lock:
            if snapshot.provider not in self._snapshots:
                raise ProviderLoadNotFoundError(
                    f"Load provider '{snapshot.provider}' is not registered"
                )
            self._snapshots[snapshot.provider] = snapshot

    def remove(self, provider: str) -> ProviderLoadSnapshot:
        """Remove and return a provider's final immutable snapshot."""
        with self._lock:
            snapshot = self.get(provider)
            del self._snapshots[provider]
            return snapshot

    def reset(self, provider: str) -> ProviderLoadSnapshot:
        """Replace a registered snapshot with an unknown zero-value snapshot."""
        with self._lock:
            self.get(provider)
            snapshot = ProviderLoadSnapshot(provider)
            self._snapshots[provider] = snapshot
            return snapshot

    def clear(self) -> None:
        """Remove every registered provider snapshot."""
        with self._lock:
            self._snapshots.clear()
