"""Bounded V7 Event Fabric-compatible metadata events."""

EVENT_TYPES = (
    "profile_registered",
    "context_registered",
    "source_federated",
    "evidence_validated",
    "evidence_rejected",
    "signal_recorded",
    "observation_recorded",
    "hypothesis_registered",
    "evaluation_completed",
    "confidence_calibrated",
    "recommendation_generated",
    "review_completed",
    "compatibility_issue_detected",
    "governance_issue_detected",
    "validation_failed",
    "lifecycle_changed",
)

__all__ = ("EVENT_TYPES",)
