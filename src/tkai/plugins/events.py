"""Immutable plugin lifecycle events using the existing observability EventBus."""

from __future__ import annotations

from dataclasses import dataclass, field

from tkai.observability import Event


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginEvent(Event):
    """Base safe event containing only plugin identifier and version."""

    plugin: str
    version: str


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginLoaded(PluginEvent):
    name: str = field(default="PluginLoaded", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginUnloaded(PluginEvent):
    name: str = field(default="PluginUnloaded", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginEnabled(PluginEvent):
    name: str = field(default="PluginEnabled", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginDisabled(PluginEvent):
    name: str = field(default="PluginDisabled", init=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PluginFailed(PluginEvent):
    name: str = field(default="PluginFailed", init=False)
