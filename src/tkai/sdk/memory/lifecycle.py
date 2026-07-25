"""Lifecycle values for explicitly managed Memory SDK implementations."""

from enum import Enum


class MemoryLifecycle(str, Enum):
    """The intentionally small lifecycle shared by reference memories."""

    CREATED = "created"
    ACTIVE = "active"
    CLOSED = "closed"
