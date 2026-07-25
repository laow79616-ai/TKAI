"""Immutable cache policies for optional manager-level integration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CachePolicy:
    """Declare read/write behavior and optional TTL without owning a backend."""

    ttl: float | None = None
    read: bool = True
    write: bool = True

    def __post_init__(self) -> None:
        if self.ttl is not None and self.ttl < 0:
            raise ValueError("cache policy ttl must not be negative")


class NoCache(CachePolicy):
    """Disable reads and writes for one explicit call path."""

    def __init__(self) -> None:
        super().__init__(ttl=None, read=False, write=False)


class ReadThrough(CachePolicy):
    """Enable cache reads and write misses produced by an explicit factory."""


class WriteThrough(CachePolicy):
    """Policy marker for callers that write through during their own operation."""
