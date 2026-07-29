"""Advisory event metadata names; this package dispatches no events."""

EVENT_NAMES = (
    "coordination.profile.registered",
    "coordination.edge.added",
    "coordination.governance.referenced",
)
DISPATCH_ENABLED = False

__all__ = ("DISPATCH_ENABLED", "EVENT_NAMES")
