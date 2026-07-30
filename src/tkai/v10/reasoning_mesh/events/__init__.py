"""V7 Event Fabric compatible internal metadata event names."""
# ruff: noqa: E501

EVENT_TYPES = tuple(
    """reasoning_profile_registered context_registered claim_registered evidence_referenced
inference_recorded assumption_registered constraint_applied_as_metadata alternative_registered
confidence_assessed uncertainty_detected contradiction_detected explanation_generated
assessment_completed validation_failed review_required lifecycle_changed""".split()
)
EVENT_FABRIC_COMPATIBILITY = "v7-event-fabric-metadata-interface"
__all__ = ("EVENT_FABRIC_COMPATIBILITY", "EVENT_TYPES")
