"""Authentication boundary for a future Studio deployment integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class StudioPrincipal:
    """Authenticated Studio identity without tying Studio to an auth provider."""

    subject: str
    display_name: str | None = None


class AuthenticationProvider(Protocol):
    """Explicit token-to-principal contract for a future Studio host."""

    def authenticate(self, token: str) -> StudioPrincipal | None: ...
