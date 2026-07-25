"""Immutable quota events published through the existing Observability EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event

from .models import RateLimitSnapshot


@dataclass(frozen=True, slots=True, kw_only=True)
class RateLimitEvent(Event):
    """Base event holding a safe immutable provider quota snapshot."""

    provider: str
    scope: str
    snapshot: RateLimitSnapshot
    reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class RateLimitExceeded(RateLimitEvent):
    """Published when a request cannot consume the local configured quota."""

    name: str = field(default="RateLimitExceeded", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class QuotaConsumed(RateLimitEvent):
    """Published after a local quota accepts and consumes a request."""

    name: str = field(default="QuotaConsumed", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class QuotaReset(RateLimitEvent):
    """Published when local observed quota usage is reset."""

    name: str = field(default="QuotaReset", init=False)
