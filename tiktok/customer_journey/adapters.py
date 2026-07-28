"""Reference-only ports for existing TikTok centers."""

from __future__ import annotations

from typing import Protocol

from .models import HandoffTarget, JourneyScope


class HandoffPort(Protocol):
    def propose(
        self, target: HandoffTarget, reference: str, scope: JourneyScope
    ) -> str: ...


class ReferenceOnlyHandoffAdapter:
    """Offline adapter that records no side effect and returns an opaque receipt."""

    def propose(
        self, target: HandoffTarget, reference: str, scope: JourneyScope
    ) -> str:
        del reference
        return f"ref://customer-journey-handoff/{target.value}/{scope.workspace}"
