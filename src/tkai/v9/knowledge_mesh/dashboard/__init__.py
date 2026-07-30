"""Read-only dashboard projection for Hyper Intelligence."""

from __future__ import annotations

from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh

DASHBOARD_SECTIONS = (
    "Knowledge Mesh Overview",
    "Profiles",
    "Federation",
    "Ontologies",
    "Taxonomies",
    "Domains",
    "Concepts",
    "Entities",
    "Relationships",
    "Knowledge",
    "Evidence",
    "Provenance",
    "Lineage",
    "Semantics",
    "Normalization",
    "Quality",
    "Confidence",
    "Versions",
    "Compatibility",
    "Governance",
    "Analytics",
    "Diagnostics",
    "Health",
    "Metrics",
    "Audit",
    "Lifecycle",
)


def dashboard_snapshot(fabric: AdaptiveKnowledgeMesh) -> dict[str, object]:
    return {"sections": DASHBOARD_SECTIONS, **fabric.snapshot()}


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
