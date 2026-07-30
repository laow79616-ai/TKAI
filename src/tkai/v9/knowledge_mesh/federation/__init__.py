"""Reference-only metadata federation."""

from tkai.v9.knowledge_mesh.aggregation import MetadataAggregator
from tkai.v9.knowledge_mesh.relationships import Relationship, RelationshipGraph

Federation = MetadataAggregator

__all__ = ("Federation", "MetadataAggregator", "Relationship", "RelationshipGraph")
