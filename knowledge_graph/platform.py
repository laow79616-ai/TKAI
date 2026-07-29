"""Secure, tenant-scoped Enterprise AI Knowledge Graph control plane."""

from __future__ import annotations

import re
import time
from collections import Counter, deque
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .metrics import KnowledgeGraphMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class GraphStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EntityType(str, Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    APPLICATION = "application"
    AGENT = "agent"
    MODEL = "model"
    DATASET = "dataset"
    WORKFLOW = "workflow"
    DOCUMENT = "document"
    ASSET = "asset"
    CUSTOM = "custom"


class RelationshipType(str, Enum):
    HIERARCHY = "hierarchy"
    REFERENCE = "reference"
    DEPENDENCY = "dependency"
    OWNERSHIP = "ownership"
    ASSOCIATION = "association"
    SIMILARITY = "similarity"
    SEMANTIC_LINK = "semantic_link"
    WEIGHTED_EDGE = "weighted_edge"


@dataclass(frozen=True, slots=True)
class GraphScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"knowledge_graph:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class KnowledgeGraph:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    version: str = "1"
    status: GraphStatus = GraphStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Entity:
    id: str
    graph_id: str
    tenant: str
    workspace: str
    name: str
    type: EntityType
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Relationship:
    id: str
    graph_id: str
    tenant: str
    workspace: str
    source_id: str
    target_id: str
    type: RelationshipType
    properties: dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Ontology:
    id: str
    graph_id: str
    tenant: str
    workspace: str
    classes: dict[str, dict[str, Any]]
    subclasses: dict[str, str] = field(default_factory=dict)
    properties: dict[str, dict[str, Any]] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    inference_rules: tuple[dict[str, Any], ...] = ()
    vocabulary: dict[str, str] = field(default_factory=dict)
    version: str = "1"


@dataclass(slots=True)
class Taxonomy:
    id: str
    graph_id: str
    tenant: str
    workspace: str
    categories: dict[str, str | None] = field(default_factory=dict)
    tags: tuple[str, ...] = ()
    labels: dict[str, str] = field(default_factory=dict)
    business_glossary: dict[str, str] = field(default_factory=dict)
    localization: dict[str, dict[str, str]] = field(default_factory=dict)


@dataclass(slots=True)
class GraphSchema:
    id: str
    graph_id: str
    tenant: str
    workspace: str
    entity_types: tuple[str, ...]
    relationship_types: tuple[str, ...]
    required_fields: dict[str, tuple[str, ...]] = field(default_factory=dict)
    optional_fields: dict[str, tuple[str, ...]] = field(default_factory=dict)
    validation: dict[str, Any] = field(default_factory=dict)
    version: str = "1"


@dataclass(slots=True)
class ProvenanceRecord:
    id: str
    graph_id: str
    subject_id: str
    tenant: str
    workspace: str
    source: str
    evidence_reference: str
    confidence: float
    owner: str
    timestamp: datetime = field(default_factory=utcnow)
    audit: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between zero and one.")


@dataclass(slots=True)
class LineageRecord:
    id: str
    graph_id: str
    subject_id: str
    tenant: str
    workspace: str
    origin: str
    transformation: str
    usage: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    version: str = "1"
    timestamp: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    timestamp: datetime
    details: dict[str, Any]


class KnowledgeGraphPlatform:
    TRANSITIONS = {
        GraphStatus.DRAFT: {GraphStatus.ACTIVE, GraphStatus.ARCHIVED},
        GraphStatus.ACTIVE: {GraphStatus.PAUSED, GraphStatus.ARCHIVED},
        GraphStatus.PAUSED: {GraphStatus.ACTIVE, GraphStatus.ARCHIVED},
        GraphStatus.ARCHIVED: {GraphStatus.DELETED},
        GraphStatus.DELETED: set(),
    }
    SECRET_KEYS = re.compile(
        r"(?:password|passwd|secret|token|api[_-]?key|authorization)", re.I
    )

    def __init__(self) -> None:
        self.graphs: dict[str, KnowledgeGraph] = {}
        self.entities: dict[str, Entity] = {}
        self.relationships: dict[str, Relationship] = {}
        self.ontologies: dict[str, Ontology] = {}
        self.taxonomies: dict[str, Taxonomy] = {}
        self.schemas: dict[str, GraphSchema] = {}
        self.provenance: list[ProvenanceRecord] = []
        self.lineage: list[LineageRecord] = []
        self.audit: list[AuditEntry] = []
        self.metrics = KnowledgeGraphMetrics()

    @staticmethod
    def _in_scope(item: Any, scope: GraphScope) -> bool:
        return bool(item.tenant == scope.tenant and item.workspace == scope.workspace)

    @staticmethod
    def _require(scope: GraphScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "knowledge_graph:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _get(self, records: dict[str, Any], item_id: str, scope: GraphScope) -> Any:
        item = records[item_id]
        if not self._in_scope(item, scope):
            raise PermissionError("Cross-tenant or cross-workspace access denied.")
        return item

    def _safe(self, value: Any) -> None:
        if isinstance(value, dict):
            if any(self.SECRET_KEYS.search(str(key)) for key in value):
                raise ValueError("Secrets are not allowed in knowledge-graph metadata.")
            for child in value.values():
                self._safe(child)
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                self._safe(child)

    def _audit(self, action: str, scope: GraphScope, **details: Any) -> None:
        self._safe(details)
        self.audit.append(
            AuditEntry(
                action,
                scope.actor,
                scope.tenant,
                scope.workspace,
                utcnow(),
                details,
            )
        )

    def create_graph(self, graph: KnowledgeGraph, scope: GraphScope) -> KnowledgeGraph:
        self._require(scope, "knowledge_graph:write")
        if not self._in_scope(graph, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if graph.id in self.graphs:
            raise ValueError("Knowledge graph already exists.")
        self._safe(graph.metadata)
        self.graphs[graph.id] = graph
        self.metrics.increment("knowledge_graphs_total")
        self._audit("graph.create", scope, graph_id=graph.id)
        return graph

    def set_status(
        self, graph_id: str, status: GraphStatus, scope: GraphScope
    ) -> KnowledgeGraph:
        self._require(scope, "knowledge_graph:write")
        graph = self._get(self.graphs, graph_id, scope)
        if status not in self.TRANSITIONS[graph.status]:
            raise ValueError("Invalid knowledge-graph lifecycle transition.")
        graph.status = status
        self._audit("graph.status", scope, graph_id=graph_id, status=status.value)
        return graph

    def add_entity(self, entity: Entity, scope: GraphScope) -> Entity:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, entity.graph_id, scope)
        if not self._in_scope(entity, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        if entity.id in self.entities:
            raise ValueError("Entity already exists.")
        self._validate_entity(entity)
        self._safe(entity.properties)
        self._safe(entity.metadata)
        self.entities[entity.id] = entity
        self.metrics.increment("knowledge_entities_total")
        self._audit("entity.create", scope, entity_id=entity.id)
        return entity

    def add_relationship(self, edge: Relationship, scope: GraphScope) -> Relationship:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, edge.graph_id, scope)
        source = self._get(self.entities, edge.source_id, scope)
        target = self._get(self.entities, edge.target_id, scope)
        if source.graph_id != edge.graph_id or target.graph_id != edge.graph_id:
            raise ValueError("Relationships cannot cross knowledge graphs.")
        if edge.id in self.relationships:
            raise ValueError("Relationship already exists.")
        if edge.weight < 0:
            raise ValueError("Relationship weight cannot be negative.")
        self._safe(edge.properties)
        self.relationships[edge.id] = edge
        self.metrics.increment("knowledge_relationships_total")
        self._audit("relationship.create", scope, relationship_id=edge.id)
        return edge

    def set_ontology(self, ontology: Ontology, scope: GraphScope) -> Ontology:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, ontology.graph_id, scope)
        if not self._in_scope(ontology, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self._safe(asdict(ontology))
        self.ontologies[ontology.graph_id] = ontology
        self._audit("ontology.set", scope, ontology_id=ontology.id)
        return ontology

    def set_taxonomy(self, taxonomy: Taxonomy, scope: GraphScope) -> Taxonomy:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, taxonomy.graph_id, scope)
        if not self._in_scope(taxonomy, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self._safe(asdict(taxonomy))
        self.taxonomies[taxonomy.graph_id] = taxonomy
        return taxonomy

    def set_schema(self, schema: GraphSchema, scope: GraphScope) -> GraphSchema:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, schema.graph_id, scope)
        if not self._in_scope(schema, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        known_entities = {item.value for item in EntityType}
        known_edges = {item.value for item in RelationshipType}
        if not set(schema.entity_types) <= known_entities:
            raise ValueError("Schema contains an unknown entity type.")
        if not set(schema.relationship_types) <= known_edges:
            raise ValueError("Schema contains an unknown relationship type.")
        self.schemas[schema.graph_id] = schema
        return schema

    def _validate_entity(self, entity: Entity) -> None:
        schema = self.schemas.get(entity.graph_id)
        if schema is None:
            return
        if entity.type.value not in schema.entity_types:
            raise ValueError("Entity type is not permitted by the graph schema.")
        missing = (
            set(schema.required_fields.get(entity.type.value, ()))
            - entity.properties.keys()
        )
        if missing:
            raise ValueError(f"Missing required entity properties: {sorted(missing)}")

    def lookup_entity(self, entity_id: str, scope: GraphScope) -> Entity:
        self._require(scope, "knowledge_graph:read")
        return self._get(self.entities, entity_id, scope)

    def lookup_relationship(
        self, relationship_id: str, scope: GraphScope
    ) -> Relationship:
        self._require(scope, "knowledge_graph:read")
        return self._get(self.relationships, relationship_id, scope)

    def _adjacency(self, graph_id: str, scope: GraphScope) -> dict[str, list[str]]:
        self._get(self.graphs, graph_id, scope)
        adjacency: dict[str, list[str]] = {}
        for edge in self.relationships.values():
            if edge.graph_id == graph_id and self._in_scope(edge, scope):
                adjacency.setdefault(edge.source_id, []).append(edge.target_id)
        return adjacency

    def traverse(
        self,
        graph_id: str,
        start_id: str,
        scope: GraphScope,
        *,
        strategy: str = "breadth_first",
        max_depth: int = 10,
        limit: int = 100,
        offset: int = 0,
        entity_type: EntityType | None = None,
    ) -> list[Entity]:
        self._require(scope, "knowledge_graph:read")
        self._get(self.entities, start_id, scope)
        if strategy not in {"breadth_first", "depth_first"}:
            raise ValueError("Unknown traversal strategy.")
        if max_depth < 0 or limit < 1 or limit > 10_000 or offset < 0:
            raise ValueError("Invalid traversal bounds.")
        adjacency = self._adjacency(graph_id, scope)
        frontier: deque[tuple[str, int]] = deque([(start_id, 0)])
        visited: set[str] = set()
        ordered: list[Entity] = []
        while frontier:
            if strategy == "breadth_first":
                node, depth = frontier.popleft()
            else:
                node, depth = frontier.pop()
            if node in visited or depth > max_depth:
                continue
            visited.add(node)
            entity = self._get(self.entities, node, scope)
            if entity_type is None or entity.type is entity_type:
                ordered.append(entity)
            for neighbor in adjacency.get(node, []):
                frontier.append((neighbor, depth + 1))
        return ordered[offset : offset + limit]

    def shortest_path(
        self,
        graph_id: str,
        source_id: str,
        target_id: str,
        scope: GraphScope,
    ) -> list[str]:
        self._require(scope, "knowledge_graph:read")
        self._get(self.entities, source_id, scope)
        self._get(self.entities, target_id, scope)
        adjacency = self._adjacency(graph_id, scope)
        queue = deque([[source_id]])
        visited = {source_id}
        while queue:
            path = queue.popleft()
            if path[-1] == target_id:
                return path
            for neighbor in adjacency.get(path[-1], []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append([*path, neighbor])
        return []

    def neighborhood(
        self,
        graph_id: str,
        entity_id: str,
        scope: GraphScope,
        *,
        depth: int = 1,
    ) -> dict[str, list[dict[str, Any]]]:
        nodes = self.traverse(graph_id, entity_id, scope, max_depth=depth)
        ids = {item.id for item in nodes}
        edges = [
            edge.to_dict()
            for edge in self.relationships.values()
            if edge.graph_id == graph_id
            and self._in_scope(edge, scope)
            and edge.source_id in ids
            and edge.target_id in ids
        ]
        return {
            "entities": [item.to_dict() for item in nodes],
            "relationships": edges,
        }

    def query(
        self,
        graph_id: str,
        scope: GraphScope,
        *,
        entity_type: EntityType | None = None,
        properties: dict[str, Any] | None = None,
        relationship_type: RelationshipType | None = None,
        limit: int = 100,
        timeout_seconds: float = 5,
    ) -> dict[str, Any]:
        self._require(scope, "knowledge_graph:query")
        if limit < 1 or limit > 10_000 or timeout_seconds <= 0 or timeout_seconds > 30:
            raise ValueError("Invalid query controls.")
        started = time.monotonic()
        self._get(self.graphs, graph_id, scope)
        matches = []
        for entity in self.entities.values():
            if time.monotonic() - started > timeout_seconds:
                raise TimeoutError("Knowledge graph query timed out.")
            if entity.graph_id != graph_id or not self._in_scope(entity, scope):
                continue
            if entity_type is not None and entity.type is not entity_type:
                continue
            if properties and any(
                entity.properties.get(key) != value for key, value in properties.items()
            ):
                continue
            matches.append(entity.to_dict())
            if len(matches) >= limit:
                break
        edges = [
            edge.to_dict()
            for edge in self.relationships.values()
            if edge.graph_id == graph_id
            and self._in_scope(edge, scope)
            and (relationship_type is None or edge.type is relationship_type)
        ][:limit]
        elapsed = time.monotonic() - started
        self.metrics.increment("knowledge_queries_total")
        self.metrics.observe("knowledge_query_latency_seconds", elapsed)
        self._audit(
            "query.execute", scope, graph_id=graph_id, result_count=len(matches)
        )
        return {
            "entities": matches,
            "relationships": edges,
            "count": len(matches),
        }

    def reason(self, graph_id: str, scope: GraphScope) -> list[dict[str, Any]]:
        """Apply declarative ontology rules; never evaluate user-provided code."""
        self._require(scope, "knowledge_graph:reason")
        ontology = self.ontologies.get(graph_id)
        inferred: list[dict[str, Any]] = []
        if ontology:
            for rule in ontology.inference_rules:
                if set(rule) - {"if_type", "then_type", "relationship"}:
                    raise ValueError("Unsupported inference rule.")
                source_type = rule.get("if_type")
                for entity in self.entities.values():
                    if entity.graph_id == graph_id and entity.type.value == source_type:
                        inferred.append(
                            {
                                "entity_id": entity.id,
                                "inferred_type": rule.get("then_type"),
                                "relationship": rule.get("relationship"),
                            }
                        )
        self.metrics.increment("knowledge_reasoning_total")
        self._audit(
            "reasoning.execute", scope, graph_id=graph_id, inferred=len(inferred)
        )
        return inferred

    def similarity(
        self,
        graph_id: str,
        entity_id: str,
        scope: GraphScope,
        *,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        source = self.lookup_entity(entity_id, scope)
        source_tokens = set(str(source.properties).lower().split())
        results = []
        for entity in self.entities.values():
            if (
                entity.id == entity_id
                or entity.graph_id != graph_id
                or not self._in_scope(entity, scope)
            ):
                continue
            tokens = set(str(entity.properties).lower().split())
            union = source_tokens | tokens
            score = len(source_tokens & tokens) / len(union) if union else 0
            results.append({"entity": entity.to_dict(), "score": score})
        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def record_provenance(
        self, record: ProvenanceRecord, scope: GraphScope
    ) -> ProvenanceRecord:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, record.graph_id, scope)
        if not self._in_scope(record, scope) or not record.evidence_reference:
            raise ValueError(
                "Scoped provenance and an evidence reference are required."
            )
        self._safe(asdict(record))
        self.provenance.append(record)
        self._audit("provenance.record", scope, provenance_id=record.id)
        return record

    def record_lineage(self, record: LineageRecord, scope: GraphScope) -> LineageRecord:
        self._require(scope, "knowledge_graph:write")
        self._get(self.graphs, record.graph_id, scope)
        if not self._in_scope(record, scope):
            raise PermissionError("Cross-tenant or cross-workspace write denied.")
        self.lineage.append(record)
        self.metrics.increment("knowledge_lineage_total")
        self._audit("lineage.record", scope, lineage_id=record.id)
        return record

    def impact_analysis(
        self, subject_id: str, scope: GraphScope
    ) -> list[dict[str, Any]]:
        self._require(scope, "knowledge_graph:read")
        impacted = [
            item
            for item in self.lineage
            if self._in_scope(item, scope) and subject_id in item.dependencies
        ]
        return [self._serialize(item) for item in impacted]

    @staticmethod
    def _serialize(item: Any) -> dict[str, Any]:
        value = asdict(item)
        for key, child in value.items():
            if isinstance(child, datetime):
                value[key] = child.isoformat()
        return value

    def analytics(self, graph_id: str, scope: GraphScope) -> dict[str, Any]:
        self._require(scope, "knowledge_graph:read")
        self._get(self.graphs, graph_id, scope)
        entities = [
            item
            for item in self.entities.values()
            if item.graph_id == graph_id and self._in_scope(item, scope)
        ]
        edges = [
            item
            for item in self.relationships.values()
            if item.graph_id == graph_id and self._in_scope(item, scope)
        ]
        degrees = Counter(edge.source_id for edge in edges)
        degrees.update(edge.target_id for edge in edges)
        centrality = {
            entity.id: degrees[entity.id] / max(1, len(entities) - 1)
            for entity in entities
        }
        result = {
            "centrality": centrality,
            "connectivity": len(edges) / max(1, len(entities)),
            "communities": self._components((entity.id for entity in entities), edges),
            "path_analysis": {"edges": len(edges), "nodes": len(entities)},
            "influence": sorted(
                centrality, key=lambda item: centrality[item], reverse=True
            ),
            "coverage": {
                "entity_types": len({entity.type for entity in entities}),
                "total_types": len(EntityType),
            },
            "growth": {"entities": len(entities), "relationships": len(edges)},
        }
        self.metrics.increment("knowledge_analytics_total")
        return result

    @staticmethod
    def _components(nodes: Iterable[str], edges: list[Relationship]) -> list[list[str]]:
        adjacency: dict[str, set[str]] = {node: set() for node in nodes}
        for edge in edges:
            adjacency.setdefault(edge.source_id, set()).add(edge.target_id)
            adjacency.setdefault(edge.target_id, set()).add(edge.source_id)
        components = []
        unseen = set(adjacency)
        while unseen:
            root = unseen.pop()
            component = {root}
            queue = deque([root])
            while queue:
                neighbors = adjacency[queue.popleft()] & unseen
                unseen -= neighbors
                component |= neighbors
                queue.extend(neighbors)
            components.append(sorted(component))
        return components

    def resource(self, name: str, scope: GraphScope) -> Any:
        self._require(scope, "knowledge_graph:read")

        def scoped(values: Iterable[Any]) -> list[Any]:
            return [item for item in values if self._in_scope(item, scope)]

        if name == "graphs":
            return [item.to_dict() for item in scoped(self.graphs.values())]
        if name == "entities":
            return [item.to_dict() for item in scoped(self.entities.values())]
        if name == "relationships":
            return [item.to_dict() for item in scoped(self.relationships.values())]
        if name == "ontology":
            return [asdict(item) for item in scoped(self.ontologies.values())]
        if name == "taxonomy":
            return [asdict(item) for item in scoped(self.taxonomies.values())]
        if name == "queries":
            return {"total": self.metrics.snapshot()["knowledge_queries_total"]}
        if name == "lineage":
            return [self._serialize(item) for item in scoped(self.lineage)]
        if name == "analytics":
            return {
                item.id: self.analytics(item.id, scope)
                for item in scoped(self.graphs.values())
            }
        raise KeyError("Unknown Knowledge Graph resource.")

    def dashboard(self, scope: GraphScope) -> dict[str, Any]:
        resources = (
            "graphs",
            "entities",
            "relationships",
            "ontology",
            "taxonomy",
            "lineage",
            "analytics",
            "queries",
        )
        return {name: self.resource(name, scope) for name in resources} | {
            "metrics": self.metrics.snapshot()
        }


EnterpriseAIKnowledgeGraphPlatform = KnowledgeGraphPlatform
