"""Immutable, safely-rendered credential data models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True, repr=False)
class Credential:
    """One resolved provider credential; its representation never exposes a key."""

    provider: str
    api_key: str
    organization: str | None = None
    base_url: str | None = None
    extra_headers: Mapping[str, str] = field(default_factory=dict, repr=False)
    source: str = "unknown"

    def __post_init__(self) -> None:
        """Reject incomplete credentials before they reach consumers."""
        if not self.provider:
            raise ValueError("Credential provider cannot be empty")
        if not self.api_key:
            raise ValueError("Credential API key cannot be empty")

    def masked(self) -> str:
        """Return a stable redacted key representation."""
        if len(self.api_key) <= 4:
            return "*" * len(self.api_key)
        return f"{self.api_key[:2]}***{self.api_key[-2:]}"

    def __repr__(self) -> str:
        """Render safe provider/source metadata only."""
        return (
            f"Credential(provider={self.provider!r}, api_key={self.masked()!r}, "
            f"source={self.source!r})"
        )
