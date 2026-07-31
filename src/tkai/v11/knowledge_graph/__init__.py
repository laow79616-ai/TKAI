"""Deterministic, immutable TKAI V11 Autonomous Knowledge Graph."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from tkai.v11.contracts import Scope
from tkai.v11.security import (
    authorize_scope,
    filter_secrets,
    security_projection,
    validate_safe_metadata,
)


def _empty_mapping() -> Mapping[str, object]:
    return MappingProxyType({})


class NodeKind(str, Enum):
    """Supported reference-only graph node kinds."""

    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    MODULE = "module"
    SERVICE = "service"
    EXTENSION = "extension"
    CONFIGURATION = "configuration"
    RUNTIME_REFERENCE = "runtime-reference"
    API = "api"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai-studio"
    POLICY = "policy"
    CONSTRAINT = "constraint"
    TRUST = "trust"
    INTEGRITY = "integrity"
    COMPATIBILITY = "compatibility"
    KNOWLEDGE = "knowledge"
    REASONING = "reasoning"
    DECISION = "decision"
    PLANNING = "planning"
    OPERATIONS = "operations"
    RECOVERY = "recovery"


class RelationshipKind(str, Enum):
    """Supported non-executable edge semantics."""

    DEPENDS_ON = "depends-on"
    REFERENCES = "references"
    COMPATIBLE_WITH = "compatible-with"
    GOVERNED_BY = "governed-by"
    TRUSTED_BY = "trusted-by"
    VERIFIED_BY = "verified-by"
    DERIVED_FROM = "derived-from"
    RELATED_TO = "related-to"
    PROTECTED_BY = "protected-by"
    OBSERVED_BY = "observed-by"


@dataclass(frozen=True, order=True)
class GraphNode:
    """Immutable metadata reference represented as a graph node."""

    node_id: str
    kind: NodeKind
    label: str
    version: str = "11.0.0"
    references: tuple[str, ...] = ()
    taxonomy: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    scope: Scope = field(default_factory=Scope, compare=False)
    executable: bool = field(default=False, init=False, compare=False)


@dataclass(frozen=True, order=True)
class GraphEdge:
    """Immutable directional relationship between metadata references."""

    edge_id: str
    source: str
    target: str
    relationship: RelationshipKind
    provenance: tuple[str, ...] = ()
    safe_metadata: Mapping[str, object] = field(
        default_factory=_empty_mapping, compare=False
    )
    scope: Scope = field(default_factory=Scope, compare=False)
    executable: bool = field(default=False, init=False, compare=False)


def _default_nodes() -> tuple[GraphNode, ...]:
    return tuple(
        GraphNode(
            node_id=f"tkai:v11:{kind.value}",
            kind=kind,
            label=kind.value.replace("-", " ").title(),
            references=(f"v10:{kind.value}",) if kind.value != "ai-studio" else (),
            taxonomy=("tkai", "v11", kind.value),
        )
        for kind in NodeKind
    )


def _default_edges() -> tuple[GraphEdge, ...]:
    root = "tkai:v11:framework"
    targets = (
        "capability",
        "module",
        "service",
        "extension",
        "configuration",
        "runtime-reference",
        "api",
        "dashboard",
        "ai-studio",
    )
    edges = [
        GraphEdge(
            edge_id=f"edge:framework:references:{target}",
            source=root,
            target=f"tkai:v11:{target}",
            relationship=RelationshipKind.REFERENCES,
            provenance=("tkai-v11-profile",),
        )
        for target in targets
    ]
    semantic_edges = (
        ("capability", "module", RelationshipKind.DEPENDS_ON),
        ("module", "service", RelationshipKind.RELATED_TO),
        ("service", "policy", RelationshipKind.GOVERNED_BY),
        ("policy", "constraint", RelationshipKind.PROTECTED_BY),
        ("trust", "integrity", RelationshipKind.VERIFIED_BY),
        ("framework", "compatibility", RelationshipKind.COMPATIBLE_WITH),
        ("knowledge", "reasoning", RelationshipKind.DERIVED_FROM),
        ("reasoning", "decision", RelationshipKind.REFERENCES),
        ("decision", "planning", RelationshipKind.RELATED_TO),
        ("planning", "operations", RelationshipKind.REFERENCES),
        ("operations", "recovery", RelationshipKind.OBSERVED_BY),
        ("integrity", "trust", RelationshipKind.TRUSTED_BY),
    )
    edges.extend(
        GraphEdge(
            edge_id=f"edge:{source}:{relationship.value}:{target}",
            source=f"tkai:v11:{source}",
            target=f"tkai:v11:{target}",
            relationship=relationship,
            provenance=("tkai-v11-ontology",),
        )
        for source, target, relationship in semantic_edges
    )
    return tuple(edges)


@dataclass(frozen=True)
class GraphProfile:
    """Complete immutable registry profile for the metadata graph."""

    graph_id: str = "tkai-v11-autonomous-knowledge-graph"
    version: str = "11.0.0"
    nodes: tuple[GraphNode, ...] = field(default_factory=_default_nodes)
    edges: tuple[GraphEdge, ...] = field(default_factory=_default_edges)
    taxonomy_registry: tuple[str, ...] = (
        "ecosystem",
        "platform",
        "runtime-reference",
        "governance",
        "intelligence-reference",
        "operations-reference",
    )
    ontology_registry: tuple[str, ...] = tuple(item.value for item in RelationshipKind)
    provenance_registry: tuple[str, ...] = (
        "tkai-v11-profile",
        "tkai-v11-ontology",
        "tkai-v10-compatibility",
    )
    lineage_registry: tuple[str, ...] = ("v6", "v7", "v8", "v9", "v10", "v11")
    validation_registry: tuple[str, ...] = (
        "unique-node-id",
        "unique-edge-id",
        "known-endpoints",
        "scope-isolation",
        "safe-metadata",
    )
    audit: tuple[Mapping[str, object], ...] = ()
    safe_metadata: Mapping[str, object] = field(default_factory=_empty_mapping)
    scope: Scope = field(default_factory=Scope)
    advisory: bool = field(default=True, init=False)
    deterministic: bool = field(default=True, init=False)
    read_only: bool = field(default=True, init=False)
    executable: bool = field(default=False, init=False)

    @property
    def node_registry(self) -> tuple[str, ...]:
        return tuple(node.node_id for node in self.nodes)

    @property
    def edge_registry(self) -> tuple[str, ...]:
        return tuple(edge.edge_id for edge in self.edges)

    @property
    def relationship_registry(self) -> tuple[str, ...]:
        return tuple(item.value for item in RelationshipKind)


class AutonomousKnowledgeGraph:
    """Read-only graph projection; deliberately exposes no mutation or traversal."""

    def __init__(
        self,
        profile: GraphProfile | None = None,
        *,
        scope: Scope | None = None,
    ) -> None:
        self._profile = profile or GraphProfile()
        self._scope = scope or self._profile.scope
        authorize_scope(self._scope, self._profile.scope)
        validate_safe_metadata(self._profile.safe_metadata)
        for node in self._profile.nodes:
            authorize_scope(self._scope, node.scope)
            validate_safe_metadata(node.safe_metadata)
        for edge in self._profile.edges:
            authorize_scope(self._scope, edge.scope)
            validate_safe_metadata(edge.safe_metadata)
        issues = self._issues()
        if issues:
            raise ValueError("; ".join(issues))

    @property
    def profile_model(self) -> GraphProfile:
        return self._profile

    def _issues(self) -> tuple[str, ...]:
        node_ids = [node.node_id for node in self._profile.nodes]
        edge_ids = [edge.edge_id for edge in self._profile.edges]
        known = set(node_ids)
        issues: list[str] = []
        if len(node_ids) != len(set(node_ids)):
            issues.append("duplicate node id")
        if len(edge_ids) != len(set(edge_ids)):
            issues.append("duplicate edge id")
        for edge in self._profile.edges:
            if edge.source not in known or edge.target not in known:
                issues.append(f"unknown edge endpoint: {edge.edge_id}")
        return tuple(sorted(issues))

    def profile(self) -> dict[str, object]:
        return {
            "graph_id": self._profile.graph_id,
            "version": self._profile.version,
            "node_registry": self._profile.node_registry,
            "edge_registry": self._profile.edge_registry,
            "relationship_registry": self._profile.relationship_registry,
            "taxonomy_registry": self._profile.taxonomy_registry,
            "ontology_registry": self._profile.ontology_registry,
            "provenance_registry": self._profile.provenance_registry,
            "lineage_registry": self._profile.lineage_registry,
            "validation_registry": self._profile.validation_registry,
            "audit": self._profile.audit,
            "health": self.health(),
            "metrics": self.metrics(),
            "safe_metadata": self._profile.safe_metadata,
            "scope": self._scope,
            "advisory": True,
            "deterministic": True,
            "read_only": True,
            "executable": False,
        }

    def nodes(self) -> dict[str, object]:
        return {"items": self._profile.nodes, "count": len(self._profile.nodes)}

    def edges(self) -> dict[str, object]:
        return {"items": self._profile.edges, "count": len(self._profile.edges)}

    def relationships(self) -> dict[str, object]:
        counts = Counter(edge.relationship.value for edge in self._profile.edges)
        return {
            "registry": self._profile.relationship_registry,
            "counts": dict(sorted(counts.items())),
            "reference_only": True,
        }

    def dependencies(self) -> dict[str, object]:
        return {
            "items": tuple(
                edge
                for edge in self._profile.edges
                if edge.relationship is RelationshipKind.DEPENDS_ON
            ),
            "execution_order": (),
            "reference_only": True,
        }

    def taxonomy(self) -> dict[str, object]:
        return {
            "registry": self._profile.taxonomy_registry,
            "node_classifications": {
                node.node_id: node.taxonomy for node in self._profile.nodes
            },
        }

    def ontology(self) -> dict[str, object]:
        return {
            "relationship_types": self._profile.ontology_registry,
            "directional": True,
            "inference_enabled": False,
        }

    def validation(self) -> dict[str, object]:
        return {
            "valid": not self._issues(),
            "issues": self._issues(),
            "checks": self._profile.validation_registry,
            "deterministic": True,
        }

    def diagnostics(self) -> dict[str, object]:
        issues = self._issues()
        return {
            "status": "clear" if not issues else "issues",
            "items": issues,
            "read_only": True,
        }

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy" if not self._issues() else "degraded",
            "metadata_ready": not self._issues(),
            "execution_ready": False,
        }

    def metrics(self) -> dict[str, int]:
        return {
            "v11_graph_nodes_total": len(self._profile.nodes),
            "v11_graph_edges_total": len(self._profile.edges),
            "v11_graph_relationship_types_total": len(RelationshipKind),
            "v11_graph_validation_failures_total": len(self._issues()),
            "v11_graph_mutations_total": 0,
        }

    def audit(self) -> dict[str, object]:
        return {"items": self._profile.audit, "append_enabled": False}

    def overview(self) -> dict[str, object]:
        return {
            "graph_id": self._profile.graph_id,
            "version": self._profile.version,
            "profile": self.profile(),
            "nodes": self.nodes(),
            "edges": self.edges(),
            "relationships": self.relationships(),
            "taxonomy": self.taxonomy(),
            "ontology": self.ontology(),
            "validation": self.validation(),
            "health": self.health(),
            "metrics": self.metrics(),
            "security": security_projection(),
            "local_first": True,
            "advisory": True,
            "deterministic": True,
            "read_only": True,
            "graph_mutation": False,
            "runtime_mutation": False,
            "external_network_calls": False,
        }

    @classmethod
    def serialize(cls, value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            value = {item.name: getattr(value, item.name) for item in fields(value)}
        if isinstance(value, Mapping):
            filtered = filter_secrets(value)
            assert isinstance(filtered, dict)
            return {str(key): cls.serialize(item) for key, item in filtered.items()}
        if isinstance(value, (tuple, list, set, frozenset)):
            items: Iterable[object] = value
            return [cls.serialize(item) for item in items]
        if isinstance(value, Enum):
            return value.value
        return value

    def projection(self, value: object) -> object:
        """Return JSON-safe, secret-filtered data for API and dashboard adapters."""
        return self.serialize(value)


__all__ = (
    "AutonomousKnowledgeGraph",
    "GraphEdge",
    "GraphNode",
    "GraphProfile",
    "NodeKind",
    "RelationshipKind",
)
