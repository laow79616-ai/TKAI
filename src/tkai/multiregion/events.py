"""Immutable region events shared through the existing EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionEvent(Event):
    region_id: str | None = None
    selected_region: str | None = None
    reason: str = ""


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionRegistered(RegionEvent):
    name: str = field(default="RegionRegistered", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionSelected(RegionEvent):
    name: str = field(default="RegionSelected", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionFallback(RegionEvent):
    name: str = field(default="RegionFallback", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionUnavailable(RegionEvent):
    name: str = field(default="RegionUnavailable", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionDisabled(RegionEvent):
    name: str = field(default="RegionDisabled", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class RegionEnabled(RegionEvent):
    name: str = field(default="RegionEnabled", init=False)
