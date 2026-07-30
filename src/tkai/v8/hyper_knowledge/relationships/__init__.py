"""Reference-only knowledge graph metadata."""

from tkai.v8.hyper_knowledge.contracts import KnowledgeRelationship


class KnowledgeGraph:
    """A registry facade with no traversal or executable graph processing."""

    def __init__(self) -> None:
        self._relationships: dict[str, KnowledgeRelationship] = {}

    def add(self, value: KnowledgeRelationship) -> KnowledgeRelationship:
        if value.relationship_id in self._relationships:
            raise ValueError(
                f"knowledge relationship already registered: {value.relationship_id}"
            )
        self._relationships[value.relationship_id] = value
        return value

    def relationships(self) -> tuple[KnowledgeRelationship, ...]:
        return tuple(
            self._relationships[key] for key in sorted(self._relationships)
        )

    @staticmethod
    def executes_graph_processing() -> bool:
        return False


__all__ = ("KnowledgeGraph", "KnowledgeRelationship")
