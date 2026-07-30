"""Read-only dashboard projection for knowledge metadata."""

from tkai.v10.knowledge_mesh import SovereignKnowledgeMesh

DASHBOARD_SECTIONS = (
    "overview",
    "domains",
    "concepts",
    "entities",
    "relationships",
    "evidence",
    "lineage",
    "compatibility",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(mesh: SovereignKnowledgeMesh) -> dict[str, object]:
    return {
        "title": "Knowledge Overview",
        "sections": DASHBOARD_SECTIONS,
        "overview": mesh.overview(),
        "domains": mesh.serialize(mesh.discover("domains")),
        "concepts": mesh.serialize(mesh.discover("concepts")),
        "entities": mesh.serialize(mesh.discover("entities")),
        "relationships": mesh.serialize(mesh.discover("relationships")),
        "evidence": mesh.serialize(mesh.discover("evidence")),
        "lineage": mesh.serialize(mesh.discover("lineage")),
        "compatibility": mesh.serialize(mesh.discover("compatibility")),
        "health": mesh.health(),
        "metrics": mesh.metrics(),
        "audit": mesh.audit(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
