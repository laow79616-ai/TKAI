"""Knowledge bases, collections, namespaces, and pluggable indexing interfaces."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    content: str
    source: str = ""
    metadata: dict[str, object] | None = None


@dataclass(frozen=True, slots=True)
class Chunk:
    document_id: str
    index: int
    content: str


class Chunker(Protocol):
    def chunk(self, document: Document) -> Sequence[Chunk]: ...


class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> Sequence[Sequence[float]]: ...


class RetrievalIndex(Protocol):
    def add(
        self,
        namespace: str,
        chunks: Sequence[Chunk],
        vectors: Sequence[Sequence[float]],
    ) -> None: ...

    def search(
        self, namespace: str, vector: Sequence[float], limit: int
    ) -> Sequence[Chunk]: ...


@dataclass(frozen=True, slots=True)
class Collection:
    collection_id: str
    name: str
    namespace: str
    documents: tuple[Document, ...] = ()


@dataclass(frozen=True, slots=True)
class KnowledgeBase:
    knowledge_id: str
    project_id: str
    name: str
    collections: tuple[Collection, ...] = ()


class KnowledgeService:
    """Coordinate ingestion through pluggable indexing interfaces."""

    def __init__(
        self,
        id_factory: Callable[[str], str],
        chunker: Chunker,
        embedder: Embedder,
        index: RetrievalIndex,
        metrics: StudioMetrics | None = None,
    ) -> None:
        self._id_factory = id_factory
        self._chunker = chunker
        self._embedder = embedder
        self._index = index
        self._metrics = metrics or StudioMetrics()
        self._items: dict[str, KnowledgeBase] = {}

    def create_base(self, project_id: str, name: str) -> KnowledgeBase:
        item = KnowledgeBase(self._id_factory("knowledge"), project_id, name)
        self._items[item.knowledge_id] = item
        return item

    def create_collection(
        self, knowledge_id: str, name: str, namespace: str
    ) -> Collection:
        base = self.get(knowledge_id)
        item = Collection(self._id_factory("collection"), name, namespace)
        self._items[knowledge_id] = KnowledgeBase(
            base.knowledge_id, base.project_id, base.name, (*base.collections, item)
        )
        return item

    def add_documents(
        self, knowledge_id: str, collection_id: str, documents: Iterable[Document]
    ) -> Collection:
        base = self.get(knowledge_id)
        incoming = tuple(documents)
        collections: list[Collection] = []
        selected: Collection | None = None
        for collection in base.collections:
            if collection.collection_id == collection_id:
                chunks = tuple(
                    chunk
                    for document in incoming
                    for chunk in self._chunker.chunk(document)
                )
                vectors = self._embedder.embed([chunk.content for chunk in chunks])
                self._index.add(collection.namespace, chunks, vectors)
                selected = Collection(
                    collection.collection_id,
                    collection.name,
                    collection.namespace,
                    (*collection.documents, *incoming),
                )
                collections.append(selected)
            else:
                collections.append(collection)
        if selected is None:
            raise KeyError(f"Collection not found: {collection_id}")
        self._items[knowledge_id] = KnowledgeBase(
            base.knowledge_id, base.project_id, base.name, tuple(collections)
        )
        self._metrics.increment("knowledge_documents", len(incoming))
        return selected

    def get(self, knowledge_id: str) -> KnowledgeBase:
        try:
            return self._items[knowledge_id]
        except KeyError as error:
            raise KeyError(f"Knowledge base not found: {knowledge_id}") from error


__all__ = (
    "Chunk",
    "Chunker",
    "Collection",
    "Document",
    "Embedder",
    "KnowledgeBase",
    "KnowledgeService",
    "RetrievalIndex",
)
