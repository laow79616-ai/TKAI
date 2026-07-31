"""V7 Event Fabric-compatible internal metadata event names."""

EVENT_TYPES = tuple(
    """decision_profile_registered context_registered option_registered
criterion_registered evaluation_registered tradeoff_registered
recommendation_registered confidence_registered
limitation_registered validation_failed review_required lifecycle_changed""".split()
)
EVENT_FABRIC_COMPATIBILITY = "v7-event-fabric-metadata-interface"

__all__ = ("EVENT_FABRIC_COMPATIBILITY", "EVENT_TYPES")
