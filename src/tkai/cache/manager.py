"""Optional cache facade; no Runtime or ProviderManager automatic takeover."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar, cast

from .keys import CacheKeyBuilder
from .memory import InMemoryBackend
from .models import CacheEntry
from .policy import CachePolicy, ReadThrough
from .registry import CacheRegistry

T = TypeVar("T")


class CacheManager:
    """Coordinate registered backends, policies, and key construction explicitly."""

    def __init__(
        self,
        registry: CacheRegistry | None = None,
        key_builder: CacheKeyBuilder | None = None,
    ) -> None:
        self.registry = registry or CacheRegistry()
        self.key_builder = key_builder or CacheKeyBuilder()
        if not self.registry.list():
            self.registry.register("memory", InMemoryBackend())

    def get(self, key: str, *, backend: str = "memory") -> CacheEntry | None:
        """Read a live cache entry through a selected backend."""
        return self.registry.get(backend).get(key)

    def set(self, entry: CacheEntry, *, backend: str = "memory") -> None:
        """Write an immutable entry through a selected backend."""
        self.registry.get(backend).set(entry)

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        *,
        provider: str | None = None,
        model: str | None = None,
        policy: CachePolicy | None = None,
        backend: str = "memory",
    ) -> T:
        """Provide opt-in read-through caching; factory is never called on a hit."""
        selected = policy or ReadThrough()
        if selected.read:
            entry = self.get(key, backend=backend)
            if entry is not None:
                return cast(T, entry.value)
        value = factory()
        if selected.write:
            self.set(
                CacheEntry(
                    key,
                    value,
                    provider=provider,
                    model=model,
                    ttl=selected.ttl,
                ),
                backend=backend,
            )
        return value

    def summary(self) -> list[dict[str, object]]:
        """Return safe backend statistics for CLI and Doctor without cached values."""
        result: list[dict[str, object]] = []
        for name, backend in self.registry.list():
            statistics = backend.statistics()
            result.append(
                {
                    "backend": name,
                    "entries": backend.size(),
                    "hit_ratio": statistics.hit_ratio,
                    "miss_ratio": statistics.miss_ratio,
                    "estimated_memory": backend.estimated_memory(),
                }
            )
        return result
