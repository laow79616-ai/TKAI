import pytest

from knowledge_graph import (
    Entity,
    EntityType,
    GraphSchema,
    GraphScope,
    GraphStatus,
    KnowledgeGraph,
    KnowledgeGraphPlatform,
    LineageRecord,
    Ontology,
    ProvenanceRecord,
    Relationship,
    RelationshipType,
)


@pytest.fixture
def platform_scope() -> tuple[KnowledgeGraphPlatform, GraphScope]:
    platform = KnowledgeGraphPlatform()
    scope = GraphScope(
        "tenant-a",
        "workspace-a",
        "owner",
        frozenset({"knowledge_graph:admin"}),
    )
    platform.create_graph(
        KnowledgeGraph(
            "g1",
            "Enterprise",
            "Knowledge",
            "tenant-a",
            "workspace-a",
            "owner",
        ),
        scope,
    )
    return platform, scope


def test_lifecycle_schema_entities_relationships_and_security(
    platform_scope: tuple[KnowledgeGraphPlatform, GraphScope],
) -> None:
    platform, scope = platform_scope
    assert (
        platform.set_status("g1", GraphStatus.ACTIVE, scope).status
        is GraphStatus.ACTIVE
    )
    platform.set_schema(
        GraphSchema(
            "s1",
            "g1",
            "tenant-a",
            "workspace-a",
            ("person", "organization"),
            ("ownership",),
            {"person": ("email",)},
        ),
        scope,
    )
    alice = Entity(
        "e1",
        "g1",
        "tenant-a",
        "workspace-a",
        "Alice",
        EntityType.PERSON,
        {"email": "a@example.test"},
    )
    company = Entity(
        "e2", "g1", "tenant-a", "workspace-a", "TKAI", EntityType.ORGANIZATION
    )
    platform.add_entity(alice, scope)
    platform.add_entity(company, scope)
    platform.add_relationship(
        Relationship(
            "r1",
            "g1",
            "tenant-a",
            "workspace-a",
            "e1",
            "e2",
            RelationshipType.OWNERSHIP,
        ),
        scope,
    )
    assert [item.id for item in platform.traverse("g1", "e1", scope)] == ["e1", "e2"]
    assert platform.shortest_path("g1", "e1", "e2", scope) == ["e1", "e2"]
    foreign = GraphScope("tenant-b", "workspace-a", "attacker")
    with pytest.raises(PermissionError):
        platform.lookup_entity("e1", foreign)
    with pytest.raises(ValueError, match="Secrets"):
        platform.add_entity(
            Entity(
                "e3",
                "g1",
                "tenant-a",
                "workspace-a",
                "Bad",
                EntityType.PERSON,
                {"email": "x", "api_key": "secret"},
            ),
            scope,
        )


def test_query_reasoning_lineage_provenance_analytics(
    platform_scope: tuple[KnowledgeGraphPlatform, GraphScope],
) -> None:
    platform, scope = platform_scope
    platform.add_entity(
        Entity("e1", "g1", "tenant-a", "workspace-a", "Alice", EntityType.PERSON),
        scope,
    )
    platform.set_ontology(
        Ontology(
            "o1",
            "g1",
            "tenant-a",
            "workspace-a",
            {"person": {}},
            inference_rules=({"if_type": "person", "then_type": "actor"},),
        ),
        scope,
    )
    assert platform.query("g1", scope, entity_type=EntityType.PERSON)["count"] == 1
    assert platform.reason("g1", scope)[0]["inferred_type"] == "actor"
    platform.record_provenance(
        ProvenanceRecord(
            "p1",
            "g1",
            "e1",
            "tenant-a",
            "workspace-a",
            "crm",
            "evidence://1",
            0.9,
            "owner",
        ),
        scope,
    )
    platform.record_lineage(
        LineageRecord("l1", "g1", "e1", "tenant-a", "workspace-a", "crm", "normalize"),
        scope,
    )
    assert platform.analytics("g1", scope)["growth"]["entities"] == 1
    metrics = platform.metrics.snapshot()
    assert metrics["knowledge_queries_total"] == 1
    assert metrics["knowledge_reasoning_total"] == 1
    assert metrics["knowledge_lineage_total"] == 1
    assert metrics["knowledge_analytics_total"] == 1
