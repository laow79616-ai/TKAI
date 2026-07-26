"""Composable RAG retrieval, ranking, context, citation, and evaluation."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from studio.metrics import StudioMetrics


@dataclass(frozen=True, slots=True)
class RetrievedDocument:
    document_id: str
    content: str
    score: float
    source: str = ""


@dataclass(frozen=True, slots=True)
class Citation:
    index: int
    document_id: str
    source: str
    excerpt: str


@dataclass(frozen=True, slots=True)
class RagResult:
    context: str
    documents: tuple[RetrievedDocument, ...]
    citations: tuple[Citation, ...]


class Retriever(Protocol):
    def retrieve(self, query: str, limit: int) -> Sequence[RetrievedDocument]: ...


class Ranker(Protocol):
    def rank(
        self, query: str, documents: Sequence[RetrievedDocument]
    ) -> Sequence[RetrievedDocument]: ...


class RagPipeline:
    """Compose retrieval interfaces without coupling to a vector database."""

    def __init__(
        self,
        retriever: Retriever,
        ranker: Ranker,
        metrics: StudioMetrics | None = None,
    ) -> None:
        self._retriever = retriever
        self._ranker = ranker
        self._metrics = metrics or StudioMetrics()

    def query(self, text: str, *, limit: int = 5, max_chars: int = 8000) -> RagResult:
        documents = tuple(
            self._ranker.rank(text, self._retriever.retrieve(text, limit))
        )
        context_parts: list[str] = []
        citations: list[Citation] = []
        used = 0
        for index, document in enumerate(documents, 1):
            remaining = max_chars - used
            if remaining <= 0:
                break
            excerpt = document.content[:remaining]
            context_parts.append(f"[{index}] {excerpt}")
            citations.append(
                Citation(index, document.document_id, document.source, excerpt[:240])
            )
            used += len(excerpt)
        self._metrics.increment("rag_queries")
        return RagResult("\n\n".join(context_parts), documents, tuple(citations))

    @staticmethod
    def evaluate(result: RagResult, relevant_ids: set[str]) -> dict[str, float]:
        retrieved = {item.document_id for item in result.documents}
        matches = len(retrieved.intersection(relevant_ids))
        return {
            "precision": matches / len(retrieved) if retrieved else 0.0,
            "recall": matches / len(relevant_ids) if relevant_ids else 0.0,
        }


__all__ = (
    "Citation",
    "RagPipeline",
    "RagResult",
    "Ranker",
    "RetrievedDocument",
    "Retriever",
)
