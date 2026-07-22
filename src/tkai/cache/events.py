"""Immutable cache events published using the existing observability EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True, kw_only=True)
class CacheEvent(Event):
    """Base safe cache event; keys are hashes and values are never included."""

    key: str
    backend: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CacheHit(CacheEvent):
    """Published when a live cache entry satisfies a read."""

    name: str = field(default="CacheHit", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class CacheMiss(CacheEvent):
    """Published when a read has no live cache entry."""

    name: str = field(default="CacheMiss", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class CacheExpired(CacheEvent):
    """Published when a read removes an expired cache entry."""

    name: str = field(default="CacheExpired", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class CacheEvicted(CacheEvent):
    """Published when an entry is explicitly deleted or cleared."""

    name: str = field(default="CacheEvicted", init=False)
