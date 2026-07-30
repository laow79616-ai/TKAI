"""Audit-only operations fabric events."""

EVENT_NAMES = (
    "operations.initialized",
    "operations.metadata.aggregated",
    "operations.metadata.registered",
)

__all__ = ("EVENT_NAMES",)
