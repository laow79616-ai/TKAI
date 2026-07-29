"""Explicit, local capability extension discovery."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v7.capabilities.contracts import CapabilityProvider


def discover(providers: Iterable[CapabilityProvider]) -> tuple[CapabilityProvider, ...]:
    """Return explicitly supplied providers without scanning or importing."""
    return tuple(providers)


__all__ = ("discover",)
