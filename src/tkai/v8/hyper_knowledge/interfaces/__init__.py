"""Read-only interfaces for knowledge metadata providers."""

from __future__ import annotations

from typing import Protocol

from tkai.v8.hyper_knowledge.contracts import KnowledgeReference


class KnowledgeMetadataProvider(Protocol):
    def discover(self) -> tuple[KnowledgeReference, ...]: ...


__all__ = ("KnowledgeMetadataProvider",)
