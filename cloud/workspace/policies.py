"""Workspace policy contracts with no authorization enforcement."""

from __future__ import annotations

from typing import Protocol

from .models import Membership


class WorkspacePolicy(Protocol):
    """Future policy boundary for caller-invoked membership validation."""

    def allows_membership(self, membership: Membership) -> bool: ...
