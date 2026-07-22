"""Immutable load state changes published through the existing EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event

from .models import LoadStatus, ProviderLoadSnapshot


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadEvent(Event):
    """Base Event carrying one immutable local load status transition."""

    provider: str
    old_status: LoadStatus
    new_status: LoadStatus
    snapshot: ProviderLoadSnapshot
    reason: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class LoadChanged(LoadEvent):
    """Published whenever the evaluator changes local provider load status."""

    name: str = field(default="LoadChanged", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderLoadHigh(LoadEvent):
    """Published when a provider transitions into HIGH local load."""

    name: str = field(default="ProviderLoadHigh", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderSaturated(LoadEvent):
    """Published when a provider transitions into SATURATED local load."""

    name: str = field(default="ProviderSaturated", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderLoadRecovered(LoadEvent):
    """Published when HIGH or SATURATED load returns to a lower status."""

    name: str = field(default="ProviderLoadRecovered", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProviderLoadReset(LoadEvent):
    """Published when a provider's local load snapshot is reset."""

    name: str = field(default="ProviderLoadReset", init=False)
