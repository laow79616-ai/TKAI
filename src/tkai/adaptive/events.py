"""Immutable adaptive-routing events published through the shared EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveEvent(Event):
    """Base event containing safe ranking and selection context."""

    provider: str | None = None
    score: float | None = None
    confidence: float | None = None
    candidate_count: int = 0
    selected_provider: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveSignalRecorded(AdaptiveEvent):
    name: str = field(default="AdaptiveSignalRecorded", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveScoreCalculated(AdaptiveEvent):
    name: str = field(default="AdaptiveScoreCalculated", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveProviderRanked(AdaptiveEvent):
    name: str = field(default="AdaptiveProviderRanked", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveProviderSelected(AdaptiveEvent):
    name: str = field(default="AdaptiveProviderSelected", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveFallbackUsed(AdaptiveEvent):
    name: str = field(default="AdaptiveFallbackUsed", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveNoProviderAvailable(AdaptiveEvent):
    name: str = field(default="AdaptiveNoProviderAvailable", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdaptiveHistoryCleared(AdaptiveEvent):
    name: str = field(default="AdaptiveHistoryCleared", init=False)
