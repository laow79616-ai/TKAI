"""Protocols for reference-only metadata sources."""

from __future__ import annotations

from typing import Protocol

from tkai.v8.hyper_intelligence.contracts import IntelligenceReference


class MetadataSource(Protocol):
    def references(self) -> tuple[IntelligenceReference, ...]: ...


__all__ = ("MetadataSource",)
