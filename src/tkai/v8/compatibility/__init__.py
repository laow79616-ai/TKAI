"""Compatibility declarations for TKAI V6, V7, and established surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CompatibilityTarget:
    """A compatibility promise exposed as metadata."""

    identifier: str
    versions: tuple[str, ...]
    mode: str = "unchanged"


DEFAULT_TARGETS = (
    CompatibilityTarget("tkai-v6", ("6.x",)),
    CompatibilityTarget("tkai-v7", ("7.x",)),
    CompatibilityTarget("tiktok-modules", ("6.x", "7.x")),
    CompatibilityTarget("openapi", ("existing",)),
    CompatibilityTarget("dashboard", ("existing",)),
    CompatibilityTarget("ai-studio", ("existing",)),
)


class CompatibilityMatrix:
    """Read-only catalog of compatibility promises."""

    def __init__(
        self, targets: tuple[CompatibilityTarget, ...] = DEFAULT_TARGETS
    ) -> None:
        self._targets = targets

    def list(self) -> tuple[CompatibilityTarget, ...]:
        return self._targets

    def supports(self, identifier: str) -> bool:
        return any(target.identifier == identifier for target in self._targets)


__all__ = ("CompatibilityMatrix", "CompatibilityTarget", "DEFAULT_TARGETS")
