"""Read-only dashboard projection for Hyper Knowledge."""

from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric

DASHBOARD_SECTIONS = (
    "Knowledge Overview",
    "Ontology",
    "Knowledge Graph",
    "Entities",
    "Relationships",
    "Evidence",
    "Lineage",
    "Compatibility",
    "Health",
    "Metrics",
    "Audit",
)


def dashboard_snapshot(fabric: HyperKnowledgeFabric) -> dict[str, object]:
    snapshot = fabric.snapshot()
    return {
        "title": "TKAI V8 Hyper Knowledge Fabric",
        "sections": DASHBOARD_SECTIONS,
        "read_only": True,
        "data": snapshot,
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
