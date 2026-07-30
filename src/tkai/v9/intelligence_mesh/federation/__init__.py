"""Reference-only metadata federation."""

from tkai.v9.intelligence_mesh.aggregation import MetadataAggregator
from tkai.v9.intelligence_mesh.relationships import Relationship, RelationshipGraph

Federation = MetadataAggregator

__all__ = ("Federation", "MetadataAggregator", "Relationship", "RelationshipGraph")
