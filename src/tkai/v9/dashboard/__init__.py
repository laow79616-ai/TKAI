"""Read-only dashboard projections."""

from tkai.v9.meta_kernel import AdaptiveMetaKernel

DASHBOARD_SECTIONS = (
    "Meta-Kernel Overview",
    "Framework Topology",
    "Capability Topology",
    "Registry",
    "Discovery",
    "Dependencies",
    "Relationships",
    "Contexts",
    "Adaptations",
    "Policies",
    "Constraints",
    "Compatibility",
    "Version Negotiation",
    "Change Plans",
    "Validation",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
    "Lifecycle",
)


def dashboard_snapshot(kernel: AdaptiveMetaKernel) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": kernel.overview(),
        "health": kernel.health(),
        "metrics": kernel.metrics(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
