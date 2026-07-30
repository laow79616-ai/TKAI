"""Metrics projection helpers."""

from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh

METRIC_NAMES = (
    "v9_knowledge_mesh_profiles_total",
    "v9_knowledge_mesh_ontologies_total",
    "v9_knowledge_mesh_taxonomies_total",
    "v9_knowledge_mesh_domains_total",
    "v9_knowledge_mesh_concepts_total",
    "v9_knowledge_mesh_entities_total",
    "v9_knowledge_mesh_relationships_total",
    "v9_knowledge_mesh_records_total",
    "v9_knowledge_mesh_evidence_total",
    "v9_knowledge_mesh_evidence_validated_total",
    "v9_knowledge_mesh_evidence_rejected_total",
    "v9_knowledge_mesh_provenance_total",
    "v9_knowledge_mesh_lineage_total",
    "v9_knowledge_mesh_compatibility_issues_total",
    "v9_knowledge_mesh_validation_failures_total",
    "v9_knowledge_mesh_quality",
    "v9_knowledge_mesh_confidence",
    "v9_knowledge_mesh_federation_seconds",
    "v9_knowledge_mesh_validation_seconds",
    "v9_knowledge_mesh_health_status",
)


def metrics_snapshot(fabric: AdaptiveKnowledgeMesh) -> dict[str, object]:
    current = fabric.metrics()
    values: dict[str, object] = {name: 0 for name in METRIC_NAMES}
    values.update(
        {
            "v9_knowledge_mesh_profiles_total": current["profiles"],
            "v9_knowledge_mesh_relationships_total": current["relationships"],
            "v9_knowledge_mesh_records_total": current["knowledge"],
            "v9_knowledge_mesh_evidence_total": current["evidence"],
            "v9_knowledge_mesh_confidence": current["confidence"],
            "v9_knowledge_mesh_health_status": 1,
        }
    )
    return values


__all__ = ("METRIC_NAMES", "metrics_snapshot")
