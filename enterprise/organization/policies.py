"""Organization policy contracts; hierarchy validation does not enforce access."""

from __future__ import annotations

from typing import Protocol

from .models import OrganizationGraph


class OrganizationPolicy(Protocol):
    """Describes an explicitly invoked organization hierarchy policy."""

    def validate(self, graph: OrganizationGraph) -> tuple[str, ...]:
        """Return deterministic validation messages without mutating the graph."""
