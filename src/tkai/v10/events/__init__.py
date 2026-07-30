"""Internal metadata events compatible with bounded V7 Event Fabric adapters."""

EVENT_NAMES = (
    "core_registered",
    "trust_domain_registered",
    "principal_registered",
    "integrity_verified",
    "integrity_failed",
    "attestation_registered",
    "boundary_registered",
    "framework_discovered",
    "capability_discovered",
    "dependency_issue_detected",
    "boundary_violation_detected",
    "policy_issue_detected",
    "compatibility_negotiated",
    "change_plan_created",
    "validation_failed",
    "review_completed",
    "approval_recorded",
    "health_degraded",
    "lifecycle_changed",
)

__all__ = ("EVENT_NAMES",)
