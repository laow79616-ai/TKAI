"""Entity, relationship, full-text, and vector-reference index interfaces."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class IndexReference:
    entity_index: str | None = None
    relationship_index: str | None = None
    full_text_index: str | None = None
    vector_reference: str | None = None
    refresh_required: bool = False
