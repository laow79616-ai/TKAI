"""Stable Sovereign Core metric names."""

METRICS = tuple(
    f"v10_sovereign_core_{suffix}"
    for suffix in (
        "trust_domains_total",
        "principals_total",
        "integrity_records_total",
        "integrity_failures_total",
        "attestations_total",
        "boundaries_total",
        "frameworks_total",
        "capabilities_total",
        "services_total",
        "modules_total",
        "extensions_total",
        "topology_nodes_total",
        "topology_edges_total",
        "dependency_issues_total",
        "boundary_violations_total",
        "compatibility_issues_total",
        "change_plans_total",
        "validation_failures_total",
        "health_status",
        "assessment_seconds",
        "compatibility_seconds",
    )
)

__all__ = ("METRICS",)
