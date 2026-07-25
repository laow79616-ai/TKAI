"""Explicit provider lifecycle state independent of concrete network clients."""

from __future__ import annotations

from enum import Enum


class ProviderLifecycle(str, Enum):
    """Observable lifecycle states for SDK provider clients."""

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"
