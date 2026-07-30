"""Internal metadata event names compatible with bounded V7 adapters."""

EVENT_NAMES = (
    "kernel_registered",
    "framework_discovered",
    "capability_discovered",
    "topology_updated_reference",
    "dependency_issue_detected",
    "compatibility_negotiated",
    "adaptation_assessed",
    "change_plan_created",
    "validation_failed",
    "review_completed",
    "approval_recorded",
    "lifecycle_changed",
    "health_degraded",
    "governance_issue_detected",
    "security_issue_detected",
)
__all__ = ("EVENT_NAMES",)
