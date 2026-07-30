"""Read-only dashboard projections."""

from typing import Protocol


class CoreProjection(Protocol):
    def overview(self) -> dict[str, object]: ...


DASHBOARD_SECTIONS = (
    "overview",
    "trust-domains",
    "identities",
    "principals",
    "integrity",
    "attestations",
    "boundaries",
    "local-control-plane",
    "frameworks",
    "capabilities",
    "services",
    "modules",
    "extensions",
    "runtime-references",
    "registries",
    "discovery",
    "topology",
    "dependencies",
    "relationships",
    "contexts",
    "policies",
    "constraints",
    "compatibility",
    "negotiation",
    "change-plans",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)


def dashboard_snapshot(core: CoreProjection) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": core.overview(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
