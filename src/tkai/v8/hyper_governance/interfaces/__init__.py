"""Protocols implemented by governance metadata providers."""

from __future__ import annotations

from typing import Protocol

from tkai.v8.hyper_governance.contracts import GovernanceReference


class GovernanceMetadataProvider(Protocol):
    def references(self) -> tuple[GovernanceReference, ...]:
        """Return references without invoking the provider runtime."""


__all__ = ("GovernanceMetadataProvider",)
