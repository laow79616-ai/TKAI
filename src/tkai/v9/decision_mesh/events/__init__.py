"""Structured, metadata-only Decision Mesh event names."""

EVENTS = frozenset(
    {
        "decision.initialized",
        "decision.sources.federated",
        "decision.record.registered",
    }
)
__all__ = ("EVENTS",)
