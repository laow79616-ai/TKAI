"""Protocols for reference-only metadata sources."""

from __future__ import annotations

from typing import Protocol

from tkai.v9.knowledge_mesh.contracts import KnowledgeReference


class MetadataSource(Protocol):
    def references(self) -> tuple[KnowledgeReference, ...]: ...


__all__ = ("MetadataSource",)
